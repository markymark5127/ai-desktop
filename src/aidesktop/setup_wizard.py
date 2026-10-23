"""Interactive first-login GNOME setup, designed for Mac-to-Linux newcomers.

This is a user-session walkthrough, not a privileged OS installer.
It never silently remaps keyboard modifiers, installs software or starts AI.
"""

from __future__ import annotations

import subprocess
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .keyboard_profiles import (
    PROFILES, KeyboardError, apply_profile_layout, get_profile,
    restore_previous_layout, set_profile, shortcut_label,
)
from .dock import DockError, POSITIONS, apply_dock, restore_dock, dock_status
from .phone_download import PHONE_APPS, qr_matrix, app_info
from .window_controls import (
    WindowLayoutError, apply_mac_layout, restore_previous_layout as restore_window_layout,
    describe_layout,
)
from .newelle_client import NewelleError, check_newelle
from .onboarding import (
    LEARNING_STYLES, PHONE_OPTIONS, get_learning_style, helper_intro,
    load_preferences, mark_setup_done, save_preferences,
    model_sharing_allowed, set_model_sharing_allowed, MODEL_SHARING_LABEL,
)
from .search import search_applications
from .themes import THEME_LABELS, SCHEMES, STYLES, load_theme, save_theme
from .mac_stoplights import install_stoplights
from .tools import ToolError, run_tool


GSCONNECT_ID = "gsconnect@andyholmes.github.io"
NEWELLE_SETUP_URL = "https://github.com/markymark5127/ai-desktop/blob/main/docs/NEWELLE_SETUP.md"
STEPS = ("Welcome", "Appearance & keyboard", "Mac-style dock", "Your helper", "AI connection", "Phone pairing", "Gaming & desktop")


class SetupWizard(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application, on_done):
        super().__init__(application=application)
        self.on_done = on_done
        self.set_title("Welcome to AI Desktop")
        self.set_default_size(740, 610)
        self.index = 0
        self.status = Gtk.Label(xalign=0)
        self.status.set_wrap(True)
        self.status.add_css_class("dim-label")

        # Paint the entire toplevel. Margins on root left the underlying white
        # Adwaita window exposed around Japandi in the original wizard.
        self.add_css_class("ai-desktop-window")
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.add_css_class("ai-desktop")
        self.theme_root = root
        toolbar = Adw.ToolbarView()
        self.set_content(toolbar)
        toolbar.set_content(root)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_margin_top(12)
        body.set_margin_bottom(18)
        body.set_margin_start(24)
        body.set_margin_end(24)

        self.css = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), self.css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        header = Gtk.HeaderBar()
        install_stoplights(self, header)
        header.set_title_widget(Gtk.Label(label="Getting started"))
        toolbar.add_top_bar(header)
        root.append(body)

        self.progress = Gtk.Label(xalign=0)
        self.progress.add_css_class("dim-label")
        body.append(self.progress)

        self.stack = Gtk.Stack()
        # Don't force all pages to retain the height of the tallest step.
        self.stack.set_vhomogeneous(False)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(180)

        for idx, make_page in enumerate(
            (self._welcome, self._appearance, self._dock, self._helper, self._model,
             self._phone, self._gaming)
        ):
            child = make_page()
            self.stack.add_named(child, f"step-{idx}")
        wrapper = Gtk.ScrolledWindow()
        wrapper.set_vexpand(True)
        wrapper.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        wrapper.set_child(self.stack)
        self.page_scroller = wrapper
        # Reset vertical scroll when a new step finishes sliding into view.
        self.stack.connect("notify::transition-running", self._on_step_transition)
        body.append(wrapper)

        body.append(self.status)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.back = Gtk.Button(label="Back")
        self.back.connect("clicked", self._go_back)
        buttons.append(self.back)

        self.skip = Gtk.Button(label="Skip setup")
        self.skip.connect("clicked", lambda *_: self._complete(True))
        buttons.append(self.skip)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        buttons.append(spacer)

        self.next = Gtk.Button(label="Continue")
        self.next.add_css_class("suggested-action")
        self.next.connect("clicked", self._go_next)
        buttons.append(self.next)
        body.append(buttons)

        self._apply_theme(load_theme())
        self._show(0)

    @staticmethod
    def _page(title: str, summary: str) -> Gtk.Box:
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_margin_top(22)
        page.set_margin_bottom(20)
        heading = Gtk.Label(label=title, xalign=0)
        heading.add_css_class("title-1")
        heading.set_wrap(True)
        page.append(heading)
        sub = Gtk.Label(label=summary, xalign=0)
        sub.set_wrap(True)
        sub.add_css_class("dim-label")
        page.append(sub)
        return page

    @staticmethod
    def _paragraph(box: Gtk.Box, text: str) -> Gtk.Label:
        label = Gtk.Label(label=text, xalign=0)
        label.set_wrap(True)
        label.set_selectable(True)
        box.append(label)
        return label

    def _apply_theme(self, name: str) -> None:
        for theme in ("japandi", "cyberpunk", "system"):
            self.remove_css_class(theme)
            self.theme_root.remove_css_class(theme)
        self.add_css_class(name)
        self.theme_root.add_css_class(name)
        manager = Adw.StyleManager.get_default()
        accessible = manager.get_high_contrast()
        self.css.load_from_data(("" if accessible else STYLES[name]).encode("utf-8"))
        scheme = "default" if accessible else SCHEMES[name]
        options = {
            "default": Adw.ColorScheme.DEFAULT,
            "light": Adw.ColorScheme.FORCE_LIGHT,
            "dark": Adw.ColorScheme.FORCE_DARK,
        }
        manager.set_color_scheme(options[scheme])

    def _welcome(self) -> Gtk.Box:
        page = self._page(
            "A familiar place to play.",
            "A Mac-familiar desktop, PC gaming, and a helping hand whenever Linux feels unfamiliar.",
        )
        self._paragraph(
            page,
            "The search shortcut opens apps immediately without AI. When something "
            "goes wrong, describe the problem and your helper can investigate "
            "supported parts of the system. It will ask before making changes.",
        )
        self._paragraph(page, "Try it now: type the name of an installed application.")
        self.try_search = Gtk.Entry()
        self.try_search.set_placeholder_text("e.g. Files, Settings, Terminal")
        page.append(self.try_search)
        self.try_matches = Gtk.Label(xalign=0)
        self.try_matches.set_wrap(True)
        page.append(self.try_matches)

        def search_changed(widget):
            query = widget.get_text().strip()
            if not query:
                self.try_matches.set_text("Search locally. This sends nothing to an AI.")
                return
            matches = search_applications(query, limit=3)
            if matches:
                self.try_matches.set_text(
                    "Found on this computer: " + ", ".join(app.name for app in matches)
                )
            else:
                self.try_matches.set_text("No matching installed applications yet.")

        self.try_search.connect("changed", search_changed)
        search_changed(self.try_search)
        return page

    def _appearance(self) -> Gtk.Box:
        page = self._page(
            "Make it feel like your Mac.",
            "Choose a look and keyboard. You can change either later.",
        )
        self._paragraph(page, "Appearance")
        self.theme_choice = Gtk.DropDown.new_from_strings(
            [label for label, _ in THEME_LABELS]
        )
        self.theme_choice.set_selected(next(
            i for i, (_label, value) in enumerate(THEME_LABELS)
            if value == load_theme()
        ))
        page.append(self.theme_choice)
        self.theme_choice.connect("notify::selected", self._theme_selected)

        self._paragraph(
            page,
            "Window controls: macOS-style red, yellow and green buttons appear "
            "on the left of AI Desktop. You can also move controls to the left "
            "in other GNOME apps (their colors may still follow their theme).",
        )
        window_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        use_mac = Gtk.Button(label="Use left-side buttons in GNOME…")
        use_mac.connect("clicked", self._confirm_window_layout)
        window_actions.append(use_mac)
        undo_mac = Gtk.Button(label="Restore original buttons")
        undo_mac.connect("clicked", lambda *_: self._run_background(restore_window_layout))
        window_actions.append(undo_mac)
        page.append(window_actions)

        self._paragraph(page, "Which keyboard are you using?")
        self.keyboard_choice = Gtk.DropDown.new_from_strings(
            [label for label, _ in PROFILES]
        )
        self.keyboard_choice.set_selected(next(
            i for i, (_label, value) in enumerate(PROFILES)
            if value == get_profile()
        ))
        self.keyboard_choice.connect("notify::selected", self._keyboard_selected)
        page.append(self.keyboard_choice)

        self.keyboard_shortcut = Gtk.Label(xalign=0)
        page.append(self.keyboard_shortcut)
        self._refresh_shortcut()

        self._paragraph(
            page, "Click the field and press your physical Command or Windows key "
            "to check whether GNOME detects it as Super. Some Windows VMs intercept the key.",
        )
        self.key_test = Gtk.Entry()
        self.key_test.set_placeholder_text("Click here, then press ⌘ Command or Win")
        page.append(self.key_test)
        self.key_feedback = Gtk.Label(xalign=0)
        self.key_feedback.set_wrap(True)
        page.append(self.key_feedback)
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._key_pressed)
        self.key_test.add_controller(keys)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        apply_button = Gtk.Button(label="Apply selected layout to GNOME…")
        apply_button.connect("clicked", self._confirm_keyboard_change)
        actions.append(apply_button)
        restore_button = Gtk.Button(label="Restore prior layout")
        restore_button.connect(
            "clicked", lambda *_: self._run_background(restore_previous_layout)
        )
        actions.append(restore_button)
        page.append(actions)
        self._paragraph(
            page,
            "Command normally acts as Super on Apple keyboards. This profile does NOT "
            "swap Ctrl+C/Ctrl+V or your terminal controls. Applying a layout is optional.",
        )
        return page

    def _confirm_window_layout(self, *_unused):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Move GNOME window controls to the top left?",
        )
        dialog.props.secondary_text = (
            "This changes your user account's GNOME window-button arrangement "
            "to Close, Minimize and Maximize on the left. It affects compatible "
            "GNOME applications, not every third-party app. AI Desktop itself "
            "uses the red/yellow/green stoplight style. The original GNOME "
            "layout is backed up and can be restored here."
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Apply", Gtk.ResponseType.OK)

        def finish(dlg, result):
            dlg.destroy()
            if result == Gtk.ResponseType.OK:
                self._run_background(apply_mac_layout)

        dialog.connect("response", finish)
        dialog.present()

    def _theme_selected(self, *_unused):
        theme = THEME_LABELS[self.theme_choice.get_selected()][1]
        try:
            save_theme(theme)
            self._apply_theme(theme)
        except OSError:
            self.status.set_text("Appearance changed for this session, but could not be saved.")

    def _keyboard_selected(self, *_unused):
        name = PROFILES[self.keyboard_choice.get_selected()][1]
        try:
            set_profile(name)
            self._refresh_shortcut()
        except OSError:
            self.status.set_text("Keyboard preference could not be saved.")

    def _refresh_shortcut(self):
        name = PROFILES[self.keyboard_choice.get_selected()][1]
        self.keyboard_shortcut.set_text(f"Your Spotlight shortcut: {shortcut_label(name)}")

    def _key_pressed(self, _controller, keyval, _keycode, state):
        super_keys = {
            Gdk.KEY_Super_L, Gdk.KEY_Super_R, Gdk.KEY_Meta_L, Gdk.KEY_Meta_R
        }
        alt_keys = {Gdk.KEY_Alt_L, Gdk.KEY_Alt_R}
        if keyval in super_keys or (state & Gdk.ModifierType.SUPER_MASK):
            self.key_feedback.set_text("Great! GNOME sees your key as Super.")
        elif keyval in alt_keys:
            self.key_feedback.set_text(
                "GNOME sees Alt, not Super. You may need to check your keyboard/VM mapping."
            )
        else:
            self.key_feedback.set_text(
                "Press Command or Windows alone; this key was not detected as Super."
            )
        return False

    def _confirm_keyboard_change(self, *_unused):
        chosen = PROFILES[self.keyboard_choice.get_selected()][1]
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.NONE,
            text="Apply this US keyboard layout?",
        )
        dialog.props.secondary_text = (
            "This changes GNOME's preferred input source while preserving your "
            "existing languages and a backup for Restore. It does not globally "
            "reassign Command, Ctrl, or Alt."
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Apply", Gtk.ResponseType.OK)

        def response(dlg, result):
            dlg.destroy()
            if result == Gtk.ResponseType.OK:
                self._run_background(lambda: apply_profile_layout(chosen))

        dialog.connect("response", response)
        dialog.present()

    def _dock(self) -> Gtk.Box:
        page = self._page(
            "Your dock, always within reach.",
            "Keep your favorite apps and a Launchpad-style Applications button "
            "visible without opening the workspace overview.",
        )
        self._paragraph(
            page,
            "GNOME's Dash to Dock extension powers this feature. It must be "
            "installed and enabled before applying settings. No system files "
            "or extensions will be installed automatically.",
        )
        self._paragraph(page, "Dock position")
        self.dock_position = Gtk.DropDown.new_from_strings(
            [name.title() for name in POSITIONS]
        )
        page.append(self.dock_position)
        self.dock_always_visible = Gtk.CheckButton(
            label="Always show dock (default)"
        )
        self.dock_always_visible.set_active(True)
        page.append(self.dock_always_visible)
        self._paragraph(
            page,
            "Show Applications (the app grid, like Launchpad) will appear in "
            "the dock. This is separate from Spotlight (Super + Space). "
            "Activities/Overview remains available for workspaces even if "
            "you later choose to hide its top-left button.",
        )
        self.dock_status_label = Gtk.Label(
            label="Dock extension status not checked yet.", xalign=0
        )
        self.dock_status_label.set_wrap(True)
        page.append(self.dock_status_label)

        check = Gtk.Button(label="Check dock extension")
        check.connect("clicked", self._check_dock)
        page.append(check)
        install_guide = Gtk.Button(label="Find Dash to Dock (GNOME Extensions)")
        install_guide.connect(
            "clicked",
            lambda *_: self._open_url("https://extensions.gnome.org/extension/307/dash-to-dock/"),
        )
        page.append(install_guide)
        apply_button = Gtk.Button(label="Apply Mac-style dock…")
        apply_button.add_css_class("suggested-action")
        apply_button.connect("clicked", self._confirm_dock)
        page.append(apply_button)
        restore = Gtk.Button(label="Restore original dock settings")
        restore.connect("clicked", lambda *_: self._run_background(restore_dock))
        page.append(restore)
        activities = Gtk.Button(label="Hide top-left Activities button (optional)")
        activities.connect(
            "clicked",
            lambda *_: self._open_url("https://extensions.gnome.org/extension/3843/just-perfection/"),
        )
        page.append(activities)
        self._paragraph(
            page,
            "Use the Just Perfection extension's Activities Button visibility "
            "setting to remove the top-left entry. It does not disable "
            "workspaces or the Super-key overview. Extension versions must "
            "be tested against your GNOME/Bazzite release.",
        )
        return page

    def _check_dock(self, *_unused):
        self.dock_status_label.set_text("Checking Dash to Dock…")

        def worker():
            try:
                message = dock_status()
            except DockError as exc:
                message = "Dock unavailable: " + str(exc)
            GLib.idle_add(self.dock_status_label.set_text, message)

        threading.Thread(target=worker, daemon=True).start()

    def _confirm_dock(self, *_unused):
        position = POSITIONS[self.dock_position.get_selected()]
        visible = self.dock_always_visible.get_active()
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.NONE,
            text="Apply the Mac-style dock layout?",
        )
        dialog.props.secondary_text = (
            f"Position: {position.title()}. "
            f"Always visible: {'Yes' if visible else 'No (auto-hide)'}. "
            "The Applications button will be enabled. This requires an "
            "already-enabled Dash to Dock extension. A backup is saved, "
            "and you can restore the previous settings."
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Apply", Gtk.ResponseType.OK)

        def confirm(dlg, result):
            dlg.destroy()
            if result == Gtk.ResponseType.OK:
                self._run_background(lambda: apply_dock(position, visible))

        dialog.connect("response", confirm)
        dialog.present()

    def _helper(self) -> Gtk.Box:
        page = self._page(
            "Your computer comes with a helping hand.",
            "Think of this as Linux training wheels, not an AI chatbot you have to learn.",
        )
        self._paragraph(
            page,
            "Search to open something, or describe what is wrong. Your helper "
            "can explain likely causes, use supported diagnostics, propose a "
            "fix and check results. It won't claim to repair something it cannot verify.",
        )
        self._paragraph(page, "How much would you like to learn along the way?")
        self.learning_choice = Gtk.DropDown.new_from_strings(
            [label for label, _ in LEARNING_STYLES]
        )
        current = get_learning_style()
        self.learning_choice.set_selected(next(
            i for i, (_label, name) in enumerate(LEARNING_STYLES) if name == current
        ))
        self.learning_choice.connect("notify::selected", self._learning_changed)
        page.append(self.learning_choice)
        self.learning_preview = Gtk.Label(xalign=0)
        self.learning_preview.set_wrap(True)
        page.append(self.learning_preview)
        self._update_learning_preview()
        self._paragraph(
            page,
            "These options change how much the helper explains. They never grant "
            "extra permissions, authorize automatic repairs, or send data to a cloud AI.",
        )
        return page

    def _learning_changed(self, *_unused):
        value = LEARNING_STYLES[self.learning_choice.get_selected()][1]
        self._update_learning_preview()
        try:
            save_preferences(learning_style=value)
        except OSError:
            self.status.set_text("Learning preference could not be saved.")

    def _update_learning_preview(self):
        value = LEARNING_STYLES[self.learning_choice.get_selected()][1]
        self.learning_preview.set_text(helper_intro(value))

    def _model(self) -> Gtk.Box:
        page = self._page(
            "Get more help when you need it.",
            "Your everyday search works without AI. Newelle can provide deeper explanations.",
        )
        self._paragraph(
            page,
            "You can use local app search without an AI model. Newelle or another "
            "selected provider may process your questions and relevant system "
            "diagnostics. Newelle can use a local or cloud model; cloud models "
            "may transfer that information off this computer.",
        )
        self.model_sharing_choice = Gtk.CheckButton(label=MODEL_SHARING_LABEL)
        self.model_sharing_choice.set_active(model_sharing_allowed())
        self.model_sharing_choice.connect("toggled", self._model_sharing_changed)
        page.append(self.model_sharing_choice)
        self._paragraph(
            page,
            "Optional and OFF by default. When enabled, pressing Enter on an "
            "Ask AI result sends the question without another confirmation. "
            "Uncheck this here or in Spotlight Settings to stop future requests. "
            "Changes to your computer still require separate approval.",
        )
        self.newelle_status = Gtk.Label(
            label="Connection not checked yet.", xalign=0
        )
        self.newelle_status.set_wrap(True)
        page.append(self.newelle_status)
        btn = Gtk.Button(label="Check headless Newelle connection")
        btn.connect("clicked", self._check_newelle)
        page.append(btn)
        guide = Gtk.Button(label="Open optional Newelle setup guide")
        guide.connect("clicked", lambda *_: self._open_url(NEWELLE_SETUP_URL))
        page.append(guide)
        self._paragraph(
            page,
            "This prototype connects only to Newelle's model endpoint, not to "
            "its unrestricted command tools. You can finish setup without it.",
        )
        return page

    def _model_sharing_changed(self, button: Gtk.CheckButton) -> None:
        allowed = button.get_active()
        try:
            set_model_sharing_allowed(allowed)
        except (OSError, ValueError):
            # Return to the last saved preference if persistence failed.
            button.set_active(model_sharing_allowed())
            self.status.set_text(
                "Couldn't save the model-sharing permission. It was not changed."
            )

    def _check_newelle(self, *_unused):
        self.newelle_status.set_text("Checking local Newelle API…")

        def work():
            try:
                result = check_newelle()
            except NewelleError as exc:
                result = "Not connected: " + str(exc)
            GLib.idle_add(self.newelle_status.set_text, result)

        threading.Thread(target=work, daemon=True).start()

    def _phone(self) -> Gtk.Box:
        page = self._page(
            "Connect your phone (optional).",
            "Bazzite GNOME may already include GSConnect; we'll check rather than reinstall it.",
        )
        self._paragraph(page, "Which phone would you like to pair?")
        self.phone_choice = Gtk.DropDown.new_from_strings(
            [label for label, _ in PHONE_OPTIONS]
        )
        current = load_preferences()["phone"]
        self.phone_choice.set_selected(next(
            i for i, (_label, name) in enumerate(PHONE_OPTIONS) if name == current
        ))
        self.phone_choice.connect("notify::selected", self._phone_selected)
        page.append(self.phone_choice)
        self.phone_details = Gtk.Label(xalign=0)
        self.phone_details.set_wrap(True)
        page.append(self.phone_details)
        # The QR is produced entirely offline and stays crisp regardless of
        # theme. GSConnect runs on the Linux desktop; scan this to install
        # KDE Connect on the phone (the actual pairing happens separately).
        self.qr_caption = Gtk.Label(xalign=0)
        self.qr_caption.set_wrap(True)
        page.append(self.qr_caption)
        self.phone_qr = Gtk.DrawingArea()
        self.phone_qr.set_content_width(208)
        self.phone_qr.set_content_height(208)
        self.phone_qr.set_size_request(208, 208)
        self.phone_qr.set_halign(Gtk.Align.CENTER)
        self.phone_qr.set_draw_func(self._draw_phone_qr)
        page.append(self.phone_qr)
        self._phone_selected(persist=False)

        self.gsconnect_status = Gtk.Label(label="GSConnect not checked yet.", xalign=0)
        self.gsconnect_status.set_wrap(True)
        page.append(self.gsconnect_status)
        check = Gtk.Button(label="Check GSConnect availability")
        check.connect("clicked", self._check_gsconnect)
        page.append(check)
        open_settings = Gtk.Button(label="Open GSConnect preferences")
        open_settings.connect("clicked", self._open_gsconnect)
        page.append(open_settings)
        self._paragraph(
            page,
            "Install KDE Connect on your phone and pair it over the same local "
            "network. Pairing is always optional; this wizard won't install "
            "an app or grant phone permissions automatically.",
        )
        return page

    def _draw_phone_qr(self, _area, cr, width, height):
        if not self.phone_qr.get_visible():
            return
        selected = PHONE_OPTIONS[self.phone_choice.get_selected()][1]
        if selected not in PHONE_APPS:
            return
        matrix = qr_matrix(selected)
        count = len(matrix)
        # Integer module sizes preserve sharp QR edges at fractional scales.
        scale = max(1, min(width, height) // count)
        edge = count * scale
        left = (width - edge) // 2
        top = (height - edge) // 2
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        cr.set_source_rgb(0, 0, 0)
        for y, row in enumerate(matrix):
            for x, dark in enumerate(row):
                if dark:
                    cr.rectangle(left + x * scale, top + y * scale, scale, scale)
        cr.fill()

    def _phone_selected(self, *_unused, persist=True):
        value = PHONE_OPTIONS[self.phone_choice.get_selected()][1]
        descriptions = {
            "iphone": (
                "iPhone supports useful manual file/link sharing and some remote "
                "controls, but not full AirDrop/Continuity, iMessage, background "
                "connection or system-wide iOS notification mirroring."
            ),
            "android": (
                "Android can offer broader KDE Connect features including "
                "notifications and clipboard integration, depending on permissions."
            ),
            "later": "You can set up GSConnect at any time in GNOME later.",
        }
        self.phone_details.set_text(descriptions[value])
        active = value in PHONE_APPS
        self.phone_qr.set_visible(active)
        if active:
            self.qr_caption.set_text(
                "Scan this QR code with your phone to install " + app_info(value)["label"]
            )
            self.phone_qr.set_tooltip_text(app_info(value)["label"])
            self.phone_qr.queue_draw()
        else:
            self.qr_caption.set_text("Phone setup skipped — no app download needed.")
        if persist:
            try:
                save_preferences(phone=value)
            except OSError:
                self.status.set_text("Phone preference could not be saved.")

    def _check_gsconnect(self, *_unused):
        self.gsconnect_status.set_text("Checking GNOME extensions…")

        def work():
            try:
                proc = subprocess.run(
                    ["gnome-extensions", "info", GSCONNECT_ID],
                    check=False, capture_output=True, text=True, timeout=4,
                )
                result = (
                    "GSConnect is present. Open its preferences to pair your phone."
                    if proc.returncode == 0
                    else "GSConnect not detected. Availability depends on GNOME and Bazzite version."
                )
            except (OSError, subprocess.TimeoutExpired):
                result = "Could not inspect GNOME extensions in this session."
            GLib.idle_add(self.gsconnect_status.set_text, result)

        threading.Thread(target=work, daemon=True).start()

    def _open_gsconnect(self, *_unused):
        try:
            subprocess.Popen(
                ["gnome-extensions", "prefs", GSCONNECT_ID],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            self.status.set_text("Requested GSConnect preferences. Pairing still requires your action.")
        except OSError:
            self.status.set_text(
                "Could not open GSConnect preferences. Check that its GNOME extension is installed."
            )

    def _gaming(self) -> Gtk.Box:
        page = self._page(
            "Ready to play. Ready to learn.",
            "Gaming comes from Bazzite and Steam; the helper is there when you need it.",
        )
        steam = next(
            (item for item in search_applications("steam", limit=12)
             if item.name.casefold() == "steam"), None
        )
        self.steam_app = steam
        if steam:
            self._paragraph(page, "Steam was found on this desktop.")
            button = Gtk.Button(label="Open Steam")
            button.connect("clicked", self._open_steam)
            page.append(button)
        else:
            self._paragraph(
                page,
                "Steam was not found in this session's application menu. "
                "That's fine in a Fedora test VM. The Bazzite image will "
                "handle supported gaming components later.",
            )
        self._paragraph(
            page,
            "GNOME can snap a window to either side by dragging it to an edge. "
            "The setup wizard can now configure an installed Dash to Dock extension "
            "for a persistent Mac-style dock. Quarter tiling and polished "
            "Shell integration remain future work.",
        )
        self._paragraph(
            page,
            "Try Super + Space (⌘ + Space on typical Apple keyboards) to open "
            "the launcher, or reopen this guide using its Setup button.",
        )
        return page

    def _open_steam(self, *_unused):
        if self.steam_app is None:
            return
        self._run_background(
            lambda: run_tool("launch_application", {"desktop_id": self.steam_app.desktop_id})
        )

    def _open_url(self, url: str):
        try:
            Gio.AppInfo.launch_default_for_uri(url, None)
        except GLib.Error:
            self.status.set_text("Could not open the setup guide in a browser.")

    def _run_background(self, operation):
        self.status.set_text("Working…")

        def worker():
            try:
                output = operation()
            except (KeyboardError, WindowLayoutError, DockError, ToolError, OSError, ValueError) as exc:
                output = f"Couldn't complete that action: {exc}"
            GLib.idle_add(self.status.set_text, output)

        threading.Thread(target=worker, daemon=True).start()

    def _reset_page_scroll(self) -> bool:
        adjustment = self.page_scroller.get_vadjustment()
        adjustment.set_value(adjustment.get_lower())
        return GLib.SOURCE_REMOVE

    def _on_step_transition(self, stack, _param) -> None:
        if not stack.get_transition_running():
            GLib.idle_add(self._reset_page_scroll)

    def _show(self, index: int):
        self.index = index
        self.stack.set_visible_child_name(f"step-{index}")
        self._reset_page_scroll()
        # After GTK recalculates the size of the new step, reset again.
        GLib.idle_add(self._reset_page_scroll)
        self.progress.set_text(f"Step {index + 1} of {len(STEPS)} · {STEPS[index]}")
        self.back.set_sensitive(index > 0)
        self.next.set_label("Finish" if index == len(STEPS) - 1 else "Continue")
        self.status.set_text("")

    def _go_back(self, *_unused):
        if self.index > 0:
            self._show(self.index - 1)

    def _go_next(self, *_unused):
        if self.index < len(STEPS) - 1:
            self._show(self.index + 1)
        else:
            self._complete(False)

    def _complete(self, skipped: bool):
        try:
            mark_setup_done(skipped=skipped)
        except OSError as exc:
            self.status.set_text(f"Could not save setup progress: {exc}")
            return
        self.on_done()
        self.close()
