"""Compact Spotlight-style GNOME launcher.

The everyday surface is a single translucent search field. Local app matches
and AI responses expand underneath only when requested. Settings remain in a
small optional popover and the complete welcome wizard stays separate.
This is a regular GTK4 window, not yet a GNOME Shell overlay/layer surface.
"""

from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .agent import Agent, AgentResponse, PendingAction
from .search import AppResult, list_applications, search_applications
from .tools import run_tool
from .themes import (
    THEME_LABELS, STYLES, SCHEMES, SPOTLIGHT_STYLES,
    SPOTLIGHT_HIGH_CONTRAST, load_theme, save_theme,
)
from .keyboard_profiles import shortcut_label, get_profile


CHOICES = [
    ("Newelle (recommended)", "newelle"),
    ("Built-in (offline)", "builtin"),
    ("Local Ollama", "local"),
    ("OpenAI API", "openai"),
    ("Claude API", "anthropic"),
]


class AssistantWindow(Adw.ApplicationWindow):
    """Small undecorated launcher; results/diagnostics appear only on demand."""

    def __init__(self, application: Adw.Application):
        super().__init__(application=application)
        self.set_title("AI Desktop Spotlight")
        self.set_default_size(640, -1)
        self.set_decorated(False)
        self.agent = Agent()
        self.pending: PendingAction | None = None
        self.catalog: list[AppResult] = list_applications()
        self.matches: list[AppResult] = []
        self.busy = False
        self._launching = False
        self.add_css_class("ai-desktop-window")
        self.add_css_class("spotlight-window")

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.add_css_class("ai-desktop")
        root.add_css_class("spotlight-shell")
        self.theme_root = root
        # Adw.ApplicationWindow uses set_content(), not GtkWindow.set_child().
        self.set_content(root)

        self._theme_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            self._theme_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.entry = Gtk.Entry()
        self.entry.add_css_class("spotlight-entry")
        self.entry.set_placeholder_text("Search apps or ask your computer…")
        self.entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, "system-search-symbolic"
        )
        self.entry.connect("changed", self._on_search_changed)
        self.entry.connect("activate", self._on_submit)
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._on_key)
        self.entry.add_controller(keys)
        search_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=0
        )
        search_row.add_css_class("spotlight-searchbar")
        self.entry.set_hexpand(True)
        search_row.append(self.entry)
        self.settings_button = Gtk.MenuButton()
        self.settings_button.add_css_class("spotlight-settings-button")
        self.settings_button.set_icon_name("preferences-system-symbolic")
        self.settings_button.set_has_frame(False)
        self.settings_button.set_tooltip_text("Preferences (Ctrl+,)")
        search_row.append(self.settings_button)
        root.append(search_row)

        self.results_section = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=0
        )
        self.results_section.add_css_class("spotlight-results")
        self.results_section.set_visible(False)
        self.results_section.append(Gtk.Separator())
        self.results = Gtk.ListBox()
        self.results.add_css_class("spotlight-list")
        self.results.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.results.connect("row-activated", self._on_result_activated)
        search_scroll = Gtk.ScrolledWindow()
        search_scroll.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC
        )
        search_scroll.set_max_content_height(260)
        search_scroll.set_propagate_natural_height(True)
        search_scroll.set_child(self.results)
        self.results_section.append(search_scroll)
        root.append(self.results_section)

        # An answer isn't a permanent conversation pane. It only expands after
        # the user explicitly asks for help or an operation returns a result.
        self.response_section = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=8
        )
        self.response_section.add_css_class("spotlight-response")
        self.response_section.set_visible(False)
        self.response_section.append(Gtk.Separator())

        response_scroll = Gtk.ScrolledWindow()
        response_scroll.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC
        )
        response_scroll.set_max_content_height(220)
        response_scroll.set_propagate_natural_height(True)
        self.output = Gtk.TextView()
        self.output.add_css_class("spotlight-output")
        self.output.set_editable(False)
        self.output.set_cursor_visible(False)
        self.output.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.output.set_left_margin(14)
        self.output.set_right_margin(14)
        self.output.set_top_margin(8)
        self.output.set_bottom_margin(8)
        response_scroll.set_child(self.output)
        self.response_section.append(response_scroll)

        approval = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        approval.add_css_class("spotlight-approval")
        self.approve_button = Gtk.Button(label="Apply change")
        self.approve_button.add_css_class("suggested-action")
        self.approve_button.connect("clicked", self._on_approve)
        self.approve_button.set_visible(False)
        approval.append(self.approve_button)
        self.cancel_button = Gtk.Button(label="Decline")
        self.cancel_button.connect("clicked", self._on_decline)
        self.cancel_button.set_visible(False)
        approval.append(self.cancel_button)
        self.response_section.append(approval)
        root.append(self.response_section)

        # Secondary icon / Ctrl+, is the only settings entry point in the bar.
        # Provider, theme, setup, and keyboard options no longer clutter search.
        self.settings = Gtk.Popover()
        self.settings.set_has_arrow(False)
        self.settings.set_autohide(True)
        self.settings.set_position(Gtk.PositionType.BOTTOM)
        self.settings_button.set_popover(self.settings)
        menu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        menu.set_margin_top(14)
        menu.set_margin_bottom(14)
        menu.set_margin_start(16)
        menu.set_margin_end(16)
        label = Gtk.Label(label="Assistant provider", xalign=0)
        menu.append(label)
        self.choice = Gtk.DropDown.new_from_strings(
            [item[0] for item in CHOICES]
        )
        menu.append(self.choice)
        menu.append(Gtk.Label(label="Appearance", xalign=0))
        self.theme_choice = Gtk.DropDown.new_from_strings(
            [label for label, _name in THEME_LABELS]
        )
        menu.append(self.theme_choice)
        self.setup_button = Gtk.Button(label="Setup & keyboard settings…")
        self.setup_button.connect("clicked", self._open_setup)
        menu.append(self.setup_button)
        self.shortcut_hint = Gtk.Label(
            label=f"Spotlight: {shortcut_label(get_profile())}  ·  "
                  "Enter: open  ·  Ctrl+Enter: ask  ·  Esc: close"
        )
        self.shortcut_hint.add_css_class("dim-label")
        self.shortcut_hint.set_wrap(True)
        menu.append(self.shortcut_hint)
        self.settings.set_child(menu)

        active_theme = load_theme()
        self.theme_choice.set_selected(
            next(i for i, (_, name) in enumerate(THEME_LABELS)
                 if name == active_theme)
        )
        self._apply_theme(active_theme)
        self.theme_choice.connect("notify::selected", self._on_theme_changed)
        self.entry.grab_focus()

    def _apply_theme(self, theme: str) -> None:
        for name in ("japandi", "cyberpunk", "system"):
            self.remove_css_class(name)
            self.theme_root.remove_css_class(name)
        self.add_css_class(theme)
        self.theme_root.add_css_class(theme)
        style_manager = Adw.StyleManager.get_default()
        accessible = style_manager.get_high_contrast()
        css = (
            SPOTLIGHT_HIGH_CONTRAST if accessible
            else STYLES[theme] + "\n" + SPOTLIGHT_STYLES[theme]
        )
        self._theme_provider.load_from_data(css.encode("utf-8"))
        scheme = "default" if accessible else SCHEMES[theme]
        schemes = {
            "light": Adw.ColorScheme.FORCE_LIGHT,
            "dark": Adw.ColorScheme.FORCE_DARK,
            "default": Adw.ColorScheme.DEFAULT,
        }
        style_manager.set_color_scheme(schemes[scheme])

    def _on_theme_changed(self, *_unused) -> None:
        theme = THEME_LABELS[self.theme_choice.get_selected()][1]
        self._apply_theme(theme)
        try:
            save_theme(theme)
        except OSError:
            self._show_text("Appearance changed, but it could not be saved.")

    def _show_settings(self) -> None:
        self.shortcut_hint.set_label(
            f"Spotlight: {shortcut_label(get_profile())}  ·  "
            "Enter: open  ·  Ctrl+Enter: ask  ·  Esc: close"
        )
        self.settings_button.popup()

    def _open_setup(self, *_unused) -> None:
        from .setup_wizard import SetupWizard
        self.settings.popdown()
        self.hide()
        wizard = SetupWizard(self.get_application(), on_done=self.present)
        wizard.present()

    def _show_text(self, message: str) -> None:
        self.results_section.set_visible(False)
        self.output.get_buffer().set_text(message)
        self.response_section.set_visible(True)
        self.queue_resize()

    def _provider(self) -> str:
        return CHOICES[self.choice.get_selected()][1]

    def _busy(self, busy: bool) -> None:
        self.busy = busy
        self.entry.set_sensitive(not busy)
        self.choice.set_sensitive(not busy)
        self.approve_button.set_sensitive(not busy)
        self.cancel_button.set_sensitive(not busy)

    def _on_search_changed(self, *_unused) -> None:
        self.response_section.set_visible(False)
        self.pending = None
        self.approve_button.set_visible(False)
        self.cancel_button.set_visible(False)
        self._update_results()

    def _update_results(self) -> None:
        query = self.entry.get_text().strip()
        if query.lower().startswith(("open ", "launch ")):
            query = query.split(" ", 1)[1].strip()
        if not query or query.lower().startswith("ask ") or "?" in query or len(query.split()) > 4:
            self.matches = []
        else:
            self.matches = search_applications(
                query, limit=5, apps=self.catalog
            )

        while child := self.results.get_row_at_index(0):
            self.results.remove(child)

        for app in self.matches:
            row = Gtk.ListBoxRow()
            content = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, spacing=12
            )
            content.set_margin_top(8)
            content.set_margin_bottom(8)
            content.set_margin_start(14)
            content.set_margin_end(14)
            image = Gtk.Image.new_from_icon_name(app.icon)
            image.set_pixel_size(24)
            content.append(image)
            labels = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, spacing=2
            )
            name = Gtk.Label(label=app.name, xalign=0)
            labels.append(name)
            if app.description:
                subtitle = Gtk.Label(
                    label=app.description[:90], xalign=0
                )
                subtitle.add_css_class("dim-label")
                subtitle.set_ellipsize(3)  # Pango.EllipsizeMode.END
                labels.append(subtitle)
            content.append(labels)
            row.set_child(content)
            self.results.append(row)

        self.results_section.set_visible(bool(self.matches))
        if self.matches:
            self.results.select_row(self.results.get_row_at_index(0))
        self.queue_resize()

    def _on_key(self, _controller, keyval, _keycode, state) -> bool:
        if keyval == Gdk.KEY_Escape:
            if self.settings.get_visible():
                self.settings.popdown()
            else:
                self.close()
            return True
        if state & Gdk.ModifierType.CONTROL_MASK:
            if keyval == Gdk.KEY_comma:
                self._show_settings()
                return True
            if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
                self._ask_ai()
                return True
        if keyval in (Gdk.KEY_Down, Gdk.KEY_Up) and self.matches:
            current = self.results.get_selected_row()
            idx = current.get_index() if current else 0
            delta = 1 if keyval == Gdk.KEY_Down else -1
            idx = max(0, min(idx + delta, len(self.matches) - 1))
            self.results.select_row(self.results.get_row_at_index(idx))
            return True
        return False

    def _on_submit(self, *_unused) -> None:
        query = self.entry.get_text().strip()
        if not query:
            return
        if self.matches and not query.lower().startswith("ask "):
            row = self.results.get_selected_row()
            idx = row.get_index() if row else 0
            self._open_app(self.matches[idx])
        else:
            self._ask_ai()

    def _on_result_activated(self, _list_box, row) -> None:
        idx = row.get_index()
        if 0 <= idx < len(self.matches):
            self._open_app(self.matches[idx])

    def _open_app(self, app: AppResult) -> None:
        self.pending = None
        self._launching = True
        self._execute(
            lambda: AgentResponse(
                run_tool("launch_application", {"desktop_id": app.desktop_id})
            )
        )

    def _ask_ai(self) -> None:
        query = self.entry.get_text().strip()
        if not query or self.busy:
            return
        if query.lower().startswith("ask "):
            query = query[4:].strip()
        if not query:
            return
        provider = self._provider()
        self.pending = None
        self._launching = False
        if provider in ("newelle", "openai", "anthropic"):
            dialog = Gtk.MessageDialog(
                transient_for=self, modal=True,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.NONE,
                text="Share this question with the selected model?",
            )
            dialog.format_secondary_text(
                "Newelle may use a local or cloud model. Prompts and diagnostic "
                "results can leave this computer, depending on its configuration. "
                "Avoid sharing passwords or personal information."
            )
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Continue", Gtk.ResponseType.OK)

            def decide(dlg, response_id):
                dlg.destroy()
                if response_id == Gtk.ResponseType.OK:
                    self._execute(lambda: self.agent.ask(query, provider))

            dialog.connect("response", decide)
            dialog.present()
        else:
            self._execute(lambda: self.agent.ask(query, provider))

    def _execute(self, operation) -> None:
        self._busy(True)
        self._show_text("Working…")

        def worker():
            try:
                response = operation()
            except Exception as exc:
                response = AgentResponse(
                    f"Request failed ({type(exc).__name__}). "
                    "Check app availability or provider settings."
                )
            GLib.idle_add(self._on_result, response)

        threading.Thread(target=worker, daemon=True).start()

    def _on_result(self, response: AgentResponse) -> bool:
        self._busy(False)
        if self._launching and response.message.startswith("Launch requested for"):
            self._launching = False
            self.close()
            return GLib.SOURCE_REMOVE
        self._launching = False
        self.pending = response.pending
        self._show_text(response.message)
        self.approve_button.set_visible(response.pending is not None)
        self.cancel_button.set_visible(response.pending is not None)
        return GLib.SOURCE_REMOVE

    def _on_approve(self, *_unused) -> None:
        action = self.pending
        self.pending = None
        self.approve_button.set_visible(False)
        self.cancel_button.set_visible(False)
        if action:
            self._execute(lambda: self.agent.approve(action))

    def _on_decline(self, *_unused) -> None:
        self.pending = None
        self.approve_button.set_visible(False)
        self.cancel_button.set_visible(False)
        self._show_text("Action declined. No settings were changed.")


class AssistantApp(Adw.Application):
    def __init__(self, *, force_setup: bool = False):
        super().__init__(
            application_id="io.github.markymark5127.AIDesktop",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.force_setup = force_setup

    def _show_launcher(self) -> None:
        window = AssistantWindow(self)
        window.present()
        window.entry.grab_focus()

    def do_activate(self) -> None:
        window = self.props.active_window
        if not window:
            from .onboarding import is_setup_done
            if self.force_setup or not is_setup_done():
                from .setup_wizard import SetupWizard
                window = SetupWizard(self, on_done=self._show_launcher)
                self.force_setup = False
            else:
                window = AssistantWindow(self)
        window.present()
        if isinstance(window, AssistantWindow):
            window.entry.grab_focus()
