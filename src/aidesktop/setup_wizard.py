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
    keyd_active, mac_shortcuts_wanted, restore_previous_layout,
    set_keyd, set_profile, shortcut_label,
)
from .dock import DockError, POSITIONS, apply_dock, restore_dock, dock_status
from .phone_download import PHONE_APPS, qr_matrix, app_info
from . import gsconnect
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
from .wallpaper import WallpaperError, apply_theme_wallpaper
from .branding import PRODUCT_NAME, WELCOME_TITLE
from .mac_stoplights import install_stoplights
from .tools import ToolError, run_tool


GSCONNECT_ID = gsconnect.GSCONNECT_ID
NEWELLE_SETUP_URL = "https://github.com/markymark5127/ai-desktop/blob/main/docs/NEWELLE_SETUP.md"
STEPS = ("Welcome", "Look and keyboard", "Your phone", "You are ready")


class SetupWizard(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application, on_done):
        super().__init__(application=application)
        self.on_done = on_done
        self.set_title(WELCOME_TITLE)
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
        # CSS providers added for the display survive window closure unless
        # explicitly removed. Without cleanup, reopening Spotlight can leave
        # old themes overriding new window/list styling.
        self.connect("close-request", self._remove_theme_provider)
        self.connect("close-request", self._stop_phone_poll)

        header = Gtk.HeaderBar()
        install_stoplights(self, header)
        header.set_title_widget(Gtk.Label(label=f"{PRODUCT_NAME} · Getting started"))
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
            (self._welcome, self._appearance, self._phone, self._ready)
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

    def _remove_theme_provider(self, *_unused) -> bool:
        Gtk.StyleContext.remove_provider_for_display(
            self.get_display(), self.css
        )
        return False

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
            f"Welcome to {PRODUCT_NAME}.",
            "This takes a minute. Super+Space opens apps and files.",
        )
        self._paragraph(page, "Try a search:")
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
            "Pick a look.",
            "Japandi is the default. You can change this later.",
        )
        self._paragraph(page, "Theme")
        self.theme_choice = Gtk.DropDown.new_from_strings(
            [label for label, _ in THEME_LABELS]
        )
        self.theme_choice.set_selected(next(
            i for i, (_label, value) in enumerate(THEME_LABELS)
            if value == load_theme()
        ))
        page.append(self.theme_choice)
        self.theme_choice.connect("notify::selected", self._theme_selected)

        self._paragraph(page, "Keyboard. Default is a Windows keyboard with Mac shortcuts.")
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
        return page

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
            "GNOME applications, not every third-party app. Mutsu Search itself "
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
        self._apply_theme(theme)
        try:
            save_theme(theme)
            self._set_branding_appearance(theme)
        except OSError:
            self.status.set_text(
                "Appearance changed for this session, but could not be saved."
            )
            return
        try:
            self.status.set_text(apply_theme_wallpaper(theme))
        except WallpaperError as exc:
            self.status.set_text(
                f"Appearance saved. Wallpaper was not changed: {exc}"
            )

    def _keyboard_selected(self, *_unused):
        name = PROFILES[self.keyboard_choice.get_selected()][1]
        try:
            set_profile(name)
            self._refresh_shortcut()
            self._run_background(lambda: set_keyd(mac_shortcuts_wanted(name)))
        except OSError:
            self.status.set_text("Keyboard preference could not be saved.")

    def _set_branding_appearance(self, theme: str) -> None:
        # Canonical setting. The branding extension reacts and applies
        # wallpaper, icons, and shell CSS. Follow System is "system".
        import subprocess
        value = theme if theme in ("japandi", "cyberpunk", "system") else "japandi"
        subprocess.run(
            ["gsettings", "set", "org.gnome.shell.extensions.mutsu-branding", "appearance", value],
            check=False, timeout=5,
        )

    def _refresh_shortcut(self):
        name = PROFILES[self.keyboard_choice.get_selected()][1]
        self.keyboard_shortcut.set_text(f"Your Mutsu Search shortcut: {shortcut_label(name)}")

    def _refresh_keyd_state(self):
        name = PROFILES[self.keyboard_choice.get_selected()][1]
        wanted = mac_shortcuts_wanted(name)
        active = keyd_active()
        if wanted:
            state = "on" if active else "off"
            self.keyd_state.set_text(f"Mac shortcuts (Super+C / Super+V): {state}")
        else:
            self.keyd_state.set_text("Mac shortcuts: off for this choice. Super+Space still opens search.")

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
                def apply():
                    apply_profile_layout(chosen)
                    return set_keyd(mac_shortcuts_wanted(chosen))
                self._run_background(apply)
                self._refresh_keyd_state()

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
            "the dock. This is separate from Mutsu Search (Super + Space). "
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
            "Meet Mutsu Mechanic.",
            "Ask for help, explanations and fixes. It's ready now.",
        )
        self._paragraph(
            page,
            "Mutsu Mechanic uses an AI model that runs on this computer, so "
            "your questions and system details stay here. App and file search "
            "work with or without it.",
        )
        self.model_sharing_choice = Gtk.CheckButton(label=MODEL_SHARING_LABEL)
        self.model_sharing_choice.set_active(model_sharing_allowed())
        self.model_sharing_choice.connect("toggled", self._model_sharing_changed)
        page.append(self.model_sharing_choice)
        self._paragraph(
            page,
            "On by default. Uncheck it here or in Mutsu Search settings to "
            "switch the AI off. Cloud AI providers stay off unless you allow "
            "them. Changes to your computer always ask first.",
        )
        self.newelle_status = Gtk.Label(
            label="Mutsu Mechanic sets itself up. Nothing to configure.", xalign=0
        )
        self.newelle_status.set_wrap(True)
        page.append(self.newelle_status)
        btn = Gtk.Button(label="Check Mutsu Mechanic")
        btn.connect("clicked", self._pair_newelle)
        page.append(btn)
        self._paragraph(
            page,
            "Mutsu generates the local token and starts the headless service. "
            "You can finish setup without it. This does not ask for a cloud key.",
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

    def _pair_newelle(self, *_unused):
        import subprocess
        self.newelle_status.set_text("Setting up Mutsu Mechanic…")
        def work():
            script = "/usr/libexec/mutsu-os/setup-newelle-user.sh"
            if not __import__("os").path.isfile(script):
                return "Pairing script is not in this image yet."
            result = subprocess.run([script], text=True, capture_output=True, timeout=120)
            text = (result.stdout or result.stderr or "Pairing finished.").strip()
            if result.returncode == 0:
                return text or "Mutsu Mechanic is ready."
            return text or "Pairing did not finish. It will retry next login."
        def done(message):
            self.newelle_status.set_text(message)
            return False
        def run():
            try:
                message = work()
            except Exception as exc:
                message = str(exc)
            GLib.idle_add(done, message)
        __import__("threading").Thread(target=run, daemon=True).start()

    def _check_newelle(self, *_unused):
        self.newelle_status.set_text("Checking Mutsu Mechanic…")

        def work():
            try:
                result = check_newelle()
            except NewelleError as exc:
                result = "Not connected: " + str(exc)
            GLib.idle_add(self.newelle_status.set_text, result)

        threading.Thread(target=work, daemon=True).start()

    def _phone(self) -> Gtk.Box:
        page = self._page(
            "Connect your phone.",
            "Share files, links and your clipboard, and see phone notifications on "
            "Android, with KDE Connect. Optional, and you can do it later.",
        )
        self._paragraph(page, "Which phone do you have?")
        self.phone_choice = Gtk.DropDown.new_from_strings(
            [label for label, _ in PHONE_OPTIONS]
        )
        current = load_preferences()["phone"]
        self.phone_choice.set_selected(next(
            i for i, (_label, name) in enumerate(PHONE_OPTIONS) if name == current
        ))
        page.append(self.phone_choice)
        self.phone_details = Gtk.Label(xalign=0)
        self.phone_details.set_wrap(True)
        self.phone_details.add_css_class("dim-label")
        page.append(self.phone_details)
        # Drawn locally from a pre-built matrix: nothing is fetched. It links to
        # KDE Connect in the phone's app store; GSConnect is the computer side.
        self.qr_caption = Gtk.Label(xalign=0.5)
        self.qr_caption.set_wrap(True)
        page.append(self.qr_caption)
        self.phone_qr = Gtk.DrawingArea()
        self.phone_qr.set_content_width(208)
        self.phone_qr.set_content_height(208)
        self.phone_qr.set_size_request(208, 208)
        self.phone_qr.set_halign(Gtk.Align.CENTER)
        self.phone_qr.set_draw_func(self._draw_phone_qr)
        page.append(self.phone_qr)
        self.phone_steps = Gtk.Label(xalign=0)
        self.phone_steps.set_wrap(True)
        page.append(self.phone_steps)
        self.gsconnect_status = Gtk.Label(xalign=0)
        self.gsconnect_status.set_wrap(True)
        page.append(self.gsconnect_status)
        # Phones GSConnect can see, with a Pair button; refreshed while this
        # step is on screen.
        self.phone_list = Gtk.ListBox()
        self.phone_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.phone_list.add_css_class("boxed-list")
        page.append(self.phone_list)
        open_settings = Gtk.Button(label="More phone settings")
        open_settings.set_halign(Gtk.Align.START)
        open_settings.connect("clicked", self._open_gsconnect)
        self.phone_more = open_settings
        page.append(open_settings)
        self._phone_enabled = False
        self._phone_poll = 0
        self._phone_seen = None
        self.phone_choice.connect("notify::selected", self._phone_selected)
        self._phone_selected(persist=False)
        self.stack.connect("notify::visible-child", self._phone_page_visibility)
        self._phone_page = page
        return page

    def _stop_phone_poll(self, *_unused):
        if getattr(self, "_phone_poll", 0):
            GLib.source_remove(self._phone_poll)
            self._phone_poll = 0
        return False

    def _phone_page_visibility(self, *_unused):
        on_page = self.stack.get_visible_child() is getattr(self, "_phone_page", None)
        choice = PHONE_OPTIONS[self.phone_choice.get_selected()][1]
        if on_page and choice in PHONE_APPS:
            self._enable_phone_connection()
            if not self._phone_poll:
                self._refresh_phones()
                self._phone_poll = GLib.timeout_add_seconds(2, self._refresh_phones)
        elif self._phone_poll:
            GLib.source_remove(self._phone_poll)
            self._phone_poll = 0

    def _enable_phone_connection(self):
        if self._phone_enabled:
            return
        self._phone_enabled = True
        self.gsconnect_status.set_text("Turning on phone connection…")

        def work():
            ok, message = gsconnect.enable_gsconnect()
            name = gsconnect.computer_name()
            GLib.idle_add(self._phone_connection_ready, ok, message, name)

        threading.Thread(target=work, daemon=True).start()

    def _phone_connection_ready(self, ok, message, name):
        self._computer_name = name
        self.gsconnect_status.set_text(message)
        if not ok:
            self._phone_enabled = False
        self._show_phone_steps()
        return GLib.SOURCE_REMOVE

    def _show_phone_steps(self):
        choice = PHONE_OPTIONS[self.phone_choice.get_selected()][1]
        if choice not in PHONE_APPS:
            self.phone_steps.set_text("")
            return
        name = getattr(self, "_computer_name", None) or gsconnect.computer_name()
        steps = gsconnect.pairing_steps(choice, name)
        self.phone_steps.set_text("\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1)))

    def _refresh_phones(self):
        def work():
            try:
                bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
                devices = gsconnect.list_devices(bus)
            except Exception:  # GSConnect still starting, or not available
                devices = None
            GLib.idle_add(self._show_phones, devices)

        threading.Thread(target=work, daemon=True).start()
        return GLib.SOURCE_CONTINUE

    def _show_phones(self, devices):
        key = None if devices is None else tuple(
            (d["path"], d["paired"], d["connected"], d["name"]) for d in devices)
        if key == self._phone_seen:
            return GLib.SOURCE_REMOVE
        self._phone_seen = key
        child = self.phone_list.get_first_child()
        while child:
            self.phone_list.remove(child)
            child = self.phone_list.get_first_child()
        if not devices:
            row = Adw.ActionRow(title="Looking for your phone…",
                                subtitle="Open KDE Connect on it, on the same Wi-Fi.")
            self.phone_list.append(row)
            return GLib.SOURCE_REMOVE
        for device in devices:
            row = Adw.ActionRow(title=device["name"], subtitle=gsconnect.device_state(device))
            if not device["paired"] and device["connected"]:
                button = Gtk.Button(label="Pair", valign=Gtk.Align.CENTER)
                button.add_css_class("suggested-action")
                button.connect("clicked", self._pair_phone, device["path"])
                row.add_suffix(button)
            elif device["paired"]:
                done = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                row.add_suffix(done)
            self.phone_list.append(row)
        if any(d["paired"] for d in devices):
            self.status.set_text("Your phone is paired. Continue when you're ready.")
        return GLib.SOURCE_REMOVE

    def _pair_phone(self, button, path):
        button.set_sensitive(False)
        button.set_label("Check your phone…")

        def work():
            try:
                bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
                gsconnect.pair(bus, path)
                message = "Pairing requested. Accept it on your phone if it asks."
            except Exception:
                message = "Couldn't send the pairing request. Try again from KDE Connect on the phone."
            GLib.idle_add(self.status.set_text, message)

        threading.Thread(target=work, daemon=True).start()

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
            "later": "You can connect a phone any time from Settings \u2192 Extensions \u2192 GSConnect.",
        }
        self.phone_details.set_text(descriptions[value])
        active = value in PHONE_APPS
        self.phone_qr.set_visible(active)
        for widget in ("phone_steps", "phone_list", "gsconnect_status", "phone_more"):
            if hasattr(self, widget):
                getattr(self, widget).set_visible(active)
        if hasattr(self, "_phone_page"):
            self._phone_page_visibility()
        if hasattr(self, "phone_steps"):
            self._show_phone_steps()
        if active:
            self.qr_caption.set_text(
                "Scan with your phone's camera to get " + app_info(value)["label"]
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


    def _ready(self) -> Gtk.Box:
        page = self._page(
            "You are ready.",
            "Press Super+Space anytime to search apps, files, and ask Mutsu Mechanic.",
        )
        self._paragraph(
            page,
            "Japandi is on, Mac shortcuts are available, and Mutsu Mechanic is ready to help. "
            "You can change the look, keyboard, dock, and phone pairing later in Settings.",
        )
        return page

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
