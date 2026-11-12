"""Compact Spotlight-style GNOME launcher.

The everyday surface is a single translucent search field. Local app matches
and AI responses expand underneath only when requested. Settings live in
GNOME Settings → Mutsu Search (Ctrl+, opens it); the welcome wizard is separate.
This is a regular GTK4 window, not yet a GNOME Shell overlay/layer surface.
"""

from __future__ import annotations

import threading
import traceback

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango  # noqa: E402

from .agent import Agent, AgentResponse, PendingAction
from .chat import Conversation, USER, MECHANIC, to_markup
from .search import AppResult, list_applications
from .search_routing import route_query, shell_manages_dismissal, should_hide_on_focus_loss
from .file_search import FileResult, list_local_files, search_local_files
from .spotlight import (
    Answer, WebAction, SettingsPage, UsageStore,
    instant_answer, web_actions, search_settings, search_file_contents,
)
from .branding import SEARCH_NAME, AI_NAME, icon_source
from .tools import run_tool
from .themes import (
    STYLES, SCHEMES, SPOTLIGHT_STYLES, SPOTLIGHT_HIGH_CONTRAST, load_theme,
)
from .onboarding import model_sharing_allowed, load_preferences
from .search_settings import PROVIDER_LABELS

GRID_SIZE = 12          # app tiles on the empty launcher, "All Apps" included
GRID_COLUMNS = 6
# Shown under usage suggestions and the dock when those are short.
DEFAULT_GRID_APPS = (
    "org.mozilla.firefox.desktop", "firefox.desktop", "org.gnome.Nautilus.desktop",
    "steam.desktop", "com.valvesoftware.Steam.desktop", "org.gnome.Ptyxis.desktop",
    "org.gnome.Settings.desktop", "io.github.kolunmi.Bazaar.desktop",
    "org.gnome.TextEditor.desktop", "org.gnome.Calendar.desktop",
    "org.gnome.Loupe.desktop", "org.gnome.Music.desktop",
)


def search_placeholder() -> str:
    return f"Search apps, files, settings, or ask {AI_NAME}…"


def grid_app_ids(catalog_ids: list[str], suggested: list[str], favorites: list[str],
                 limit: int = GRID_SIZE - 1) -> list[str]:
    """Launcher tiles: what you use now, then your dock, then Mutsu's picks,
    then anything else, without repeats and only apps that exist."""
    known = set(catalog_ids)
    out: list[str] = []
    for desktop_id in [*suggested, *favorites, *DEFAULT_GRID_APPS, *catalog_ids]:
        if desktop_id in known and desktop_id not in out:
            out.append(desktop_id)
        if len(out) >= limit:
            break
    return out


def dock_favorites() -> list[str]:
    source = Gio.SettingsSchemaSource.get_default()
    if source is None or source.lookup("org.gnome.shell", True) is None:
        return []
    return list(Gio.Settings(schema_id="org.gnome.shell").get_strv("favorite-apps"))


class AssistantWindow(Adw.ApplicationWindow):
    """Small undecorated launcher; results/diagnostics appear only on demand."""

    def __init__(self, application: Adw.Application):
        super().__init__(application=application)
        self.set_title(SEARCH_NAME)
        self.set_default_size(700, -1)
        self.set_decorated(False)
        # Gtk.Window:is-active becomes False after another app or the desktop
        # receives focus. A short deferred check avoids closing for our own
        # preferences popover and permission dialogs.
        self.connect("notify::is-active", self._on_active_changed)
        self.agent = Agent()
        self.pending: PendingAction | None = None
        # Asking Mechanic turns this window into a chat (see _enter_chat).
        self.conversation = Conversation()
        self.chat_mode = False
        self._thinking: Gtk.Widget | None = None
        self.catalog: list[AppResult] = list_applications()
        self.usage = UsageStore()
        self._content_query = ""
        self._content_results: list = []
        self._content_timer = 0
        self.matches: list[AppResult] = []
        # Index filenames in a bounded background task, never on each key.
        self.files_catalog: list[FileResult] = []
        self.targets: list[AppResult | FileResult | str | None] = []
        self.selectable_indices: list[int] = []
        self.busy = False
        self._ever_active = False
        self._pending_dismiss = False
        self._opening_setup = False
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
        # CSS providers added for the display survive window closure unless
        # explicitly removed. Without cleanup, reopening Spotlight can leave
        # old themes overriding new window/list styling.
        self.connect("close-request", self._remove_theme_provider)

        self.entry = Gtk.Entry()
        self.entry.add_css_class("spotlight-entry")
        self.entry.set_placeholder_text(search_placeholder())
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
        self.shortcut_hint = Gtk.Label(label="Super + Space")
        self.shortcut_hint.add_css_class("spotlight-hint")
        self.shortcut_hint.set_valign(Gtk.Align.CENTER)
        search_row.append(self.shortcut_hint)
        root.append(search_row)
        self.search_row = search_row
        self.entry.connect("icon-press", self._on_entry_icon)

        root.append(self._build_launchpad())

        self.results_section = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=0
        )
        self.results_section.add_css_class("spotlight-results")
        self.results_section.set_visible(False)
        self.results_divider = Gtk.Separator()
        self.results_section.append(self.results_divider)
        self.results = Gtk.ListBox()
        self.results.add_css_class("spotlight-list")
        self.results.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.results.connect("row-activated", self._on_result_activated)
        search_scroll = Gtk.ScrolledWindow()
        search_scroll.add_css_class("spotlight-scroll")
        search_scroll.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC
        )
        search_scroll.set_max_content_height(430)
        search_scroll.set_propagate_natural_height(True)
        search_scroll.set_child(self.results)
        self.results_section.append(search_scroll)
        # Shortcuts only prefill the search; pressing Enter is still required
        # to send anything to Newelle or another configured AI.
        self.suggestion_chips = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=7
        )
        self.suggestion_chips.add_css_class("spotlight-chips")
        self.suggestion_chips.set_margin_start(12)
        self.suggestion_chips.set_margin_end(12)
        self.suggestion_chips.set_margin_top(0)
        self.suggestion_chips.set_margin_bottom(10)
        for label, prefix in (
            ("Explain this", "Explain "),
            ("Troubleshoot", "Help me troubleshoot "),
        ):
            chip = Gtk.Button(label=label)
            chip.add_css_class("spotlight-chip")
            chip.connect(
                "clicked", lambda _btn, pre=prefix: self._prefill_ai(pre)
            )
            self.suggestion_chips.append(chip)
        self.suggestion_chips.set_visible(False)
        self.results_section.append(self.suggestion_chips)
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

        root.append(self._build_chat())

        # Settings (provider, privacy, web search, look) live in GNOME
        # Settings → Mutsu Search and are read fresh whenever they're used.
        self._apply_theme(load_theme())
        self.entry.grab_focus()
        GLib.idle_add(self._begin_file_scan)

    # ---- launchpad: the empty launcher is a grid of apps --------------------

    def _build_launchpad(self) -> Gtk.Widget:
        self.launchpad = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.launchpad.add_css_class("spotlight-launchpad")
        self.app_grid = Gtk.FlowBox()
        self.app_grid.add_css_class("spotlight-grid")
        self.app_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        self.app_grid.set_homogeneous(True)
        self.app_grid.set_min_children_per_line(GRID_COLUMNS)
        self.app_grid.set_max_children_per_line(GRID_COLUMNS)
        self.app_grid.set_row_spacing(4)
        self.app_grid.set_column_spacing(4)
        self.app_grid.connect("child-activated", self._on_tile_activated)
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._on_grid_key)
        self.app_grid.add_controller(keys)
        self.launchpad.append(self.app_grid)
        self.grid_targets: list[AppResult | str] = []
        self._fill_launchpad()
        return self.launchpad

    def _tile(self, label: str, icon_name: str, size: int = 48) -> Gtk.FlowBoxChild:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add_css_class("spotlight-tile-box")
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(size)
        icon.set_halign(Gtk.Align.CENTER)
        icon.add_css_class("spotlight-tile-icon")
        box.append(icon)
        name = Gtk.Label(label=label, justify=Gtk.Justification.CENTER)
        name.set_ellipsize(Pango.EllipsizeMode.END)
        name.set_max_width_chars(11)
        name.add_css_class("spotlight-tile-label")
        box.append(name)
        child = Gtk.FlowBoxChild()
        child.add_css_class("spotlight-tile")
        child.set_child(box)
        child.set_tooltip_text(label)
        return child

    def _fill_launchpad(self) -> None:
        while child := self.app_grid.get_child_at_index(0):
            self.app_grid.remove(child)
        by_id = {app.desktop_id: app for app in self.catalog}
        try:
            favorites = dock_favorites()
        except GLib.Error:
            favorites = []
        ids = grid_app_ids(list(by_id), self.usage.suggestions(list(by_id), limit=GRID_SIZE),
                           favorites)
        self.grid_targets = [by_id[d] for d in ids] + ["all-apps"]
        for target in self.grid_targets:
            if target == "all-apps":
                tile = self._tile("All Apps", "view-app-grid-symbolic", 28)
                tile.add_css_class("spotlight-all-apps")
            else:
                tile = self._tile(target.name, target.icon)
            self.app_grid.append(tile)

    def _on_tile_activated(self, _grid, child) -> None:
        index = child.get_index()
        if not 0 <= index < len(self.grid_targets):
            return
        target = self.grid_targets[index]
        if target == "all-apps":
            self._show_all_apps()
        else:
            self._open_app(target)

    def _show_all_apps(self) -> None:
        """GNOME's own app grid, like the dock's Show Apps button."""
        try:
            Gio.bus_get_sync(Gio.BusType.SESSION, None).call(
                "org.gnome.Shell", "/org/gnome/Shell", "org.gnome.Shell",
                "ShowApplications", None, None, Gio.DBusCallFlags.NONE, 2000, None, None)
        except GLib.Error as exc:
            self._show_text(f"Could not open the app grid: {exc.message}")
            return
        self.close()

    def _on_grid_key(self, controller, keyval, _keycode, _state) -> bool:
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        focused = self.app_grid.get_focus_child()
        index = focused.get_index() if focused else 0
        if keyval == Gdk.KEY_Up and index < GRID_COLUMNS:
            self.entry.grab_focus_without_selecting()
            return True
        if Gdk.keyval_to_unicode(keyval) and keyval not in (Gdk.KEY_space, Gdk.KEY_Return):
            # Typing from the grid searches, as it does from the field.
            self.entry.grab_focus_without_selecting()
            return controller.forward(self.entry.get_delegate() or self.entry)
        return False

    # ---- chat with Mutsu Mechanic -------------------------------------------

    def _build_chat(self) -> Gtk.Widget:
        """Header, message bubbles and approval row. Hidden until someone asks
        Mechanic; then it slides open and the search field moves under it to
        become the reply box."""
        self.chat_revealer = Gtk.Revealer()
        self.chat_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.chat_revealer.set_transition_duration(220)
        self.chat_revealer.set_reveal_child(False)
        self.chat_revealer.set_visible(False)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add_css_class("mechanic-chat")

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.add_css_class("mechanic-header")
        back = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        back.add_css_class("flat")
        back.set_tooltip_text("Back to search (Esc)")
        back.connect("clicked", lambda *_: self._leave_chat())
        header.append(back)
        icon_path = icon_source("mutsu-ai.svg", "mutsu-logo-symbol.svg")
        avatar = (Gtk.Image.new_from_file(str(icon_path)) if icon_path is not None
                  else Gtk.Image.new_from_icon_name("dialog-question-symbolic"))
        avatar.set_pixel_size(22)
        header.append(avatar)
        title = Gtk.Label(label=AI_NAME, xalign=0)
        title.add_css_class("mechanic-title")
        title.set_hexpand(True)
        header.append(title)
        new_chat = Gtk.Button.new_from_icon_name("list-add-symbolic")
        new_chat.add_css_class("flat")
        new_chat.set_tooltip_text("New chat")
        new_chat.connect("clicked", lambda *_: self._new_chat())
        header.append(new_chat)
        box.append(header)

        self.chat_scroll = Gtk.ScrolledWindow()
        self.chat_scroll.add_css_class("mechanic-scroll")
        self.chat_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.chat_scroll.set_min_content_height(160)
        self.chat_scroll.set_max_content_height(440)
        self.chat_scroll.set_propagate_natural_height(True)
        self.chat_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.chat_list.add_css_class("mechanic-messages")
        self.chat_scroll.set_child(self.chat_list)
        box.append(self.chat_scroll)

        approval = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        approval.add_css_class("spotlight-approval")
        self.chat_approve = Gtk.Button(label="Apply change")
        self.chat_approve.add_css_class("suggested-action")
        self.chat_approve.connect("clicked", self._on_approve)
        self.chat_decline = Gtk.Button(label="Decline")
        self.chat_decline.connect("clicked", self._on_decline)
        approval.append(self.chat_approve)
        approval.append(self.chat_decline)
        self.chat_approval = approval
        approval.set_visible(False)
        box.append(approval)

        self.chat_revealer.set_child(box)
        return self.chat_revealer

    def _bubble(self, role: str, text: str) -> Gtk.Widget:
        label = Gtk.Label(xalign=0, wrap=True, selectable=True)
        label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(54)
        if role == MECHANIC:
            label.set_markup(to_markup(text))
        else:
            label.set_text(text)
        bubble = Gtk.Box()
        bubble.add_css_class("mechanic-bubble")
        bubble.add_css_class("from-user" if role == USER else "from-mechanic")
        bubble.set_halign(Gtk.Align.END if role == USER else Gtk.Align.START)
        bubble.append(label)
        return bubble

    def _append_bubble(self, role: str, text: str) -> None:
        self.chat_list.append(self._bubble(role, text))
        self._scroll_chat_to_end()

    def _scroll_chat_to_end(self) -> None:
        self._relayout()  # grow with the conversation, up to the scroll limit

        def scroll() -> bool:
            adj = self.chat_scroll.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())
            return GLib.SOURCE_REMOVE
        GLib.idle_add(scroll)

    def _show_thinking(self) -> None:
        self._hide_thinking()
        label = Gtk.Label(label=f"{AI_NAME} is thinking…", xalign=0)
        bubble = Gtk.Box()
        bubble.add_css_class("mechanic-bubble")
        bubble.add_css_class("from-mechanic")
        bubble.add_css_class("thinking")
        bubble.set_halign(Gtk.Align.START)
        bubble.append(label)
        self._thinking = bubble
        self.chat_list.append(bubble)
        self._scroll_chat_to_end()

    def _hide_thinking(self) -> None:
        if self._thinking is not None:
            self.chat_list.remove(self._thinking)
            self._thinking = None

    def _clear_bubbles(self) -> None:
        self._thinking = None
        while child := self.chat_list.get_first_child():
            self.chat_list.remove(child)

    def _enter_chat(self) -> None:
        if self.chat_mode:
            return
        if self.conversation.stale():
            self.conversation.clear()
            self._clear_bubbles()
        self.chat_mode = True
        self.results_section.set_visible(False)
        self.response_section.set_visible(False)
        self.add_css_class("chatting")
        self.theme_root.add_css_class("chatting")
        # The search field slides under the chat and becomes the reply box.
        self.theme_root.reorder_child_after(self.search_row, self.chat_revealer)
        self.launchpad.set_visible(False)
        self.shortcut_hint.set_visible(False)
        self.entry.set_placeholder_text(f"Reply to {AI_NAME}…")
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, None)
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "mail-send-symbolic")
        self.entry.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, "Send")
        self.chat_revealer.set_visible(True)
        self.chat_revealer.set_reveal_child(True)
        self._relayout()

    def _leave_chat(self) -> None:
        if not self.chat_mode:
            return
        self.chat_mode = False
        self.pending = None
        self.chat_approval.set_visible(False)
        self.conversation.clear()
        self._clear_bubbles()
        self.remove_css_class("chatting")
        self.theme_root.remove_css_class("chatting")
        self.chat_revealer.set_reveal_child(False)
        self.chat_revealer.set_visible(False)
        self.theme_root.reorder_child_after(self.search_row, None)
        self.shortcut_hint.set_visible(True)
        self.entry.set_placeholder_text(search_placeholder())
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, None)
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "system-search-symbolic")
        self.entry.set_text("")
        self._update_results()
        self.entry.grab_focus()

    def _new_chat(self) -> None:
        if self.busy:
            return
        self.pending = None
        self.chat_approval.set_visible(False)
        self.conversation.clear()
        self._clear_bubbles()
        self._append_bubble(MECHANIC, "New chat. What can I help with?")
        self.entry.grab_focus()

    def _on_entry_icon(self, _entry, position) -> None:
        if self.chat_mode and position == Gtk.EntryIconPosition.SECONDARY:
            self._send_chat()

    def _send_chat(self) -> None:
        text = self.entry.get_text().strip()
        if text.lower().startswith("ask "):
            text = text[4:].strip()
        if not text or self.busy:
            return
        provider = self._provider()
        if provider != "builtin" and not model_sharing_allowed(provider):
            self._append_bubble(MECHANIC, self._ai_off_message())
            return
        history = self.conversation.history()
        self.conversation.add(USER, text)
        self._append_bubble(USER, text)
        self.entry.set_text("")
        self.pending = None
        self.chat_approval.set_visible(False)
        self._launching = False
        self._execute(lambda: self.agent.ask(text, provider, history))

    def _ai_off_message(self) -> str:
        return (
            ("Cloud AI is off. Turn on cloud AI models in Settings → "
             "Mutsu Search (Ctrl+,) to use this provider. ")
            if model_sharing_allowed() else
            ("Mutsu Mechanic's AI is switched off. Turn it on in Settings → "
             "Mutsu Search (Ctrl+,). ")
        ) + "App search and built-in checks still work."

    def _begin_file_scan(self) -> bool:
        def worker() -> None:
            files = list_local_files()
            GLib.idle_add(self._on_file_scan_finished, files)
        threading.Thread(target=worker, daemon=True).start()
        return GLib.SOURCE_REMOVE

    def _on_file_scan_finished(self, files: list[FileResult]) -> bool:
        self.files_catalog = files
        if self.entry.get_text().strip() and self.get_visible():
            self._update_results()
        return GLib.SOURCE_REMOVE

    def _remove_theme_provider(self, *_unused) -> bool:
        Gtk.StyleContext.remove_provider_for_display(
            self.get_display(), self._theme_provider
        )
        return False

    def _on_active_changed(self, *_unused) -> None:
        if self._opening_setup:
            return
        if self.is_active():
            self._ever_active = True
            return
        if self._ever_active and not self._pending_dismiss:
            self._pending_dismiss = True
            GLib.timeout_add(150, self._dismiss_if_unfocused)

    def _dismiss_if_unfocused(self) -> bool:
        self._pending_dismiss = False
        if self._opening_setup:
            return GLib.SOURCE_REMOVE
        if shell_manages_dismissal():
            # Mutsu's Shell extension hides Search on outside taps and app
            # switches, and knows that taps on the on-screen keyboard (or
            # its button) are typing, which this window cannot tell.
            return GLib.SOURCE_REMOVE
        if should_hide_on_focus_loss(
            activated_once=self._ever_active,
            is_active=self.is_active(),
            is_visible=self.get_visible(),
            modal_dialog=False,
            settings_open=False,
        ):
            # For ordinary Spotlight searches, CLOSE instead of just hiding.
            # That releases the old GNOME app instance so a later shortcut
            # starts current code (important while developing). Preserve a
            # hidden window only for an in-flight request or approval.
            if self.busy or self.pending is not None or (self.chat_mode and len(self.conversation)):
                self.hide()
            else:
                self.close()
        return GLib.SOURCE_REMOVE

    def prepare_activation(self) -> None:
        if self.chat_mode:
            # Coming back to a recent chat picks it up; an old one starts over.
            if self.busy or self.pending is not None or not self.conversation.stale():
                self.entry.grab_focus()
                return
            self._leave_chat()
        if not self.busy and self.pending is None:
            self.entry.set_text("")
            self.response_section.set_visible(False)
            self.results_section.set_visible(False)
            self._fill_launchpad()  # suggestions follow the time of day
            self._update_results()

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

    def _show_settings(self) -> None:
        """Ctrl+, opens Settings → Mutsu Search (the wizard if that's missing)."""
        try:
            Gio.Subprocess.new(["gnome-control-center", "mutsu-search"],
                               Gio.SubprocessFlags.NONE)
        except GLib.Error:
            self._open_setup()
            return
        self.close()

    def _open_setup(self, *_unused) -> None:
        """Leave Spotlight visible until the complete wizard is presented.

        Popovers can cause GTK/Wayland focus changes; run navigation on the
        next idle instead of changing application windows inside their click
        handler. An exception must never strand the user with an empty desktop.
        """
        if self._opening_setup:
            return
        self._opening_setup = True
        GLib.idle_add(self._present_setup)

    def _present_setup(self) -> bool:
        try:
            app = self.get_application()
            if app is None:
                raise RuntimeError("Spotlight is no longer attached to the application")
            app.open_setup_from(self)
        except Exception as exc:
            traceback.print_exc()
            self._show_text(
                f"Couldn't open Setup & keyboard settings ({type(exc).__name__}): "
                f"{exc}. You can also use: bash scripts/run-dev.sh --setup"
            )
            self.present()
        finally:
            self._opening_setup = False
        return GLib.SOURCE_REMOVE

    def _relayout(self) -> None:
        # Clearing GTK's cached height prevents the window remaining the size
        # of a previous long AI response after returning to an empty search.
        self.set_default_size(700, -1)
        self.queue_resize()

    def _show_text(self, message: str) -> None:
        self.results_section.set_visible(False)
        self.output.get_buffer().set_text(message)
        self.response_section.set_visible(True)
        self._relayout()

    def _provider(self) -> str:
        return str(load_preferences()["provider"])

    def _busy(self, busy: bool) -> None:
        self.busy = busy
        self.entry.set_sensitive(not busy)
        self.approve_button.set_sensitive(not busy)
        self.cancel_button.set_sensitive(not busy)
        if hasattr(self, "chat_approve"):
            self.chat_approve.set_sensitive(not busy)
            self.chat_decline.set_sensitive(not busy)

    def _on_search_changed(self, *_unused) -> None:
        if self.chat_mode:
            return  # typing a reply, not searching
        self.response_section.set_visible(False)
        self.pending = None
        self.approve_button.set_visible(False)
        self.cancel_button.set_visible(False)
        self._update_results()

    def _prefill_ai(self, prefix: str) -> None:
        current = self.entry.get_text().strip()
        if not current:
            return
        if current.casefold().startswith(prefix.casefold()):
            self.entry.grab_focus()
            return
        self.entry.set_text(prefix + current)
        self.entry.set_position(-1)
        self.entry.grab_focus()

    def _append_heading(self, title: str) -> None:
        """Noninteractive group label inside the same scrollable results list."""
        row = Gtk.ListBoxRow()
        row.add_css_class("spotlight-section-row")
        row.set_selectable(False)
        row.set_activatable(False)
        heading = Gtk.Label(label=title, xalign=0)
        heading.add_css_class("spotlight-section-heading")
        heading.set_margin_start(14)
        heading.set_margin_end(14)
        heading.set_margin_top(9)
        heading.set_margin_bottom(3)
        row.set_child(heading)
        self.results.append(row)
        self.targets.append("section")

    def _append_result(self, row: Gtk.ListBoxRow, target) -> None:
        self.results.append(row)
        self.targets.append(target)
        self.selectable_indices.append(len(self.targets) - 1)

    def _make_result(
        self, title: str, subtitle: str, icon_name: str,
        *, css_class: str,
    ) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        row.add_css_class("spotlight-result-row")
        row.add_css_class(css_class)
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        content.set_margin_top(8)
        content.set_margin_bottom(8)
        content.set_margin_start(14)
        content.set_margin_end(14)
        icon_path = icon_source("mutsu-ai.svg", "mutsu-logo-symbol.svg") if (
            css_class == "spotlight-ask-row"
        ) else None
        icon = (
            Gtk.Image.new_from_file(str(icon_path))
            if icon_path is not None
            else Gtk.Image.new_from_icon_name(icon_name)
        )
        icon.set_pixel_size(28)
        content.append(icon)
        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        labels.set_hexpand(True)
        labels.set_valign(Gtk.Align.CENTER)
        name = Gtk.Label(label=title, xalign=0)
        name.set_ellipsize(Pango.EllipsizeMode.END)
        labels.append(name)
        if subtitle:
            description = Gtk.Label(label=subtitle[:110], xalign=0)
            description.add_css_class("dim-label")
            description.add_css_class("spotlight-result-subtitle")
            description.set_ellipsize(Pango.EllipsizeMode.END)
            labels.append(description)
        content.append(labels)
        row.set_child(content)
        return row

    def _engine(self) -> str:
        return str(load_preferences()["search_engine"])

    def _schedule_content_search(self, query: str) -> None:
        """Search file contents (LocalSearch index) off the UI thread."""
        if self._content_timer:
            GLib.source_remove(self._content_timer)
            self._content_timer = 0
        if len(query) < 3 or query == self._content_query:
            return

        def start() -> bool:
            self._content_timer = 0

            def worker() -> None:
                paths = search_file_contents(query)
                GLib.idle_add(self._on_content_results, query, paths)
            threading.Thread(target=worker, daemon=True).start()
            return GLib.SOURCE_REMOVE
        self._content_timer = GLib.timeout_add(250, start)

    def _on_content_results(self, query: str, paths) -> bool:
        if self.entry.get_text().strip() != query:
            return GLib.SOURCE_REMOVE  # the user kept typing
        self._content_query = query
        self._content_results = paths
        self._update_results()
        return GLib.SOURCE_REMOVE

    def _update_results(self) -> None:
        query = self.entry.get_text().strip()
        route = route_query(query, self.catalog, limit=4)
        # Apps you use often (and around this time of day) rank first.
        self.matches = sorted(route.apps, key=lambda a: -self.usage.score(a.desktop_id))
        self.targets = []
        self.selectable_indices = []
        answer = instant_answer(query) if query else None
        file_matches = []
        settings_matches = []
        content_matches = []
        searchable = query and not query.casefold().startswith("ask ") and "?" not in query
        if searchable:
            file_matches = search_local_files(query, self.files_catalog, limit=4)
            settings_matches = search_settings(query)
            self._schedule_content_search(query)
            if query == self._content_query:
                named = {f.path for f in file_matches}
                content_matches = [p for p in self._content_results if p not in named][:4]
        while child := self.results.get_row_at_index(0):
            self.results.remove(child)

        # An empty launcher shows the app grid (suggestions first) instead.
        self.launchpad.set_visible(not query and not self.chat_mode)

        if answer:
            self._append_heading("Calculator" if answer.title.count(" ") <= 1 else "Conversion")
            self._append_result(self._make_result(
                answer.title, answer.subtitle, "accessories-calculator-symbolic",
                css_class="spotlight-answer-row"), answer)

        if self.matches:
            self._append_heading("Top Results")
            for app in self.matches:
                self._append_result(
                    self._make_result(
                        app.name, app.description or "Application",
                        app.icon, css_class="spotlight-app-row"
                    ), app
                )

        if settings_matches:
            self._append_heading("Settings")
            for page in settings_matches:
                self._append_result(self._make_result(
                    page.title, "Settings", "preferences-system-symbolic",
                    css_class="spotlight-settings-row"), page)

        if file_matches:
            self._append_heading("Files")
            for file in file_matches:
                suffix = file.path.suffix.casefold()
                icon_name = (
                    "folder-symbolic" if file.is_dir else
                    "image-x-generic-symbolic" if suffix in (
                        ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"
                    ) else "text-x-generic-symbolic"
                )
                self._append_result(
                    self._make_result(
                        file.name, file.subtitle, icon_name,
                        css_class="spotlight-file-row"
                    ), file
                )

        if content_matches:
            self._append_heading("In Documents")
            home = GLib.get_home_dir()
            for path in content_matches:
                folder = str(path.parent).replace(home, "~", 1)
                self._append_result(self._make_result(
                    path.name, f"Contains “{query[:40]}” · {folder}",
                    "x-office-document-symbolic", css_class="spotlight-file-row"),
                    FileResult(path, path.name, folder, False))

        if query and not query.casefold().startswith("ask "):
            actions = web_actions(query, self._engine())
            if actions:
                self._append_heading("Web")
                for action in actions:
                    self._append_result(self._make_result(
                        action.title, action.subtitle, "web-browser-symbolic",
                        css_class="spotlight-web-row"), action)

        if route.offer_ai:
            self._append_heading("AI Suggestions")
            chosen = self._provider()
            provider = PROVIDER_LABELS.get(chosen, "assistant").replace(" (on this computer)", "")
            row = self._make_result(
                f"Ask {AI_NAME}",
                f"Via {provider} · {route.query[:75]}",
                "dialog-question-symbolic",
                css_class="spotlight-ask-row",
            )
            self._append_result(row, None)

        any_results = bool(self.selectable_indices)
        ai_only = route.offer_ai and len(self.selectable_indices) == 1
        self.results_divider.set_visible(False)
        if ai_only:
            self.results_section.add_css_class("spotlight-ai-only")
        else:
            self.results_section.remove_css_class("spotlight-ai-only")
        self.results_section.set_visible(any_results)
        self.suggestion_chips.set_visible(bool(route.offer_ai and query))
        if self.selectable_indices:
            self.results.select_row(
                self.results.get_row_at_index(self.selectable_indices[0])
            )
        self._relayout()

    def _on_key(self, _controller, keyval, _keycode, state) -> bool:
        if keyval == Gdk.KEY_Escape:
            if self.chat_mode:
                # Esc goes back to search; mid-answer it just hides the
                # window so the answer is waiting when Search reopens.
                if self.busy:
                    self.hide()
                else:
                    self._leave_chat()
                return True
            self.close()
            return True
        # Enter is enough for both launch and AI; there is no special AI
        # hotkey. Only Settings retains its Ctrl/Command+, shortcut.
        if (state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SUPER_MASK)
                and keyval == Gdk.KEY_comma):
            self._show_settings()
            return True
        if (keyval == Gdk.KEY_Down and self.launchpad.get_visible()
                and not self.entry.get_text().strip()):
            first = self.app_grid.get_child_at_index(0)
            if first is not None:
                first.grab_focus()
                return True
        if keyval in (Gdk.KEY_Down, Gdk.KEY_Up) and self.selectable_indices:
            current = self.results.get_selected_row()
            index = current.get_index() if current else -1
            try:
                position = self.selectable_indices.index(index)
            except ValueError:
                position = 0
            delta = 1 if keyval == Gdk.KEY_Down else -1
            position = max(
                0, min(position + delta, len(self.selectable_indices) - 1)
            )
            self.results.select_row(
                self.results.get_row_at_index(self.selectable_indices[position])
            )
            return True
        return False

    def _on_submit(self, *_unused) -> None:
        if self.chat_mode:
            self._send_chat()
            return
        query = self.entry.get_text().strip()
        if not query:
            return
        row = self.results.get_selected_row()
        idx = row.get_index() if row else 0
        if 0 <= idx < len(self.targets):
            self._activate_target(self.targets[idx])
        else:
            self._ask_ai()

    def _on_result_activated(self, _list_box, row) -> None:
        idx = row.get_index()
        if 0 <= idx < len(self.targets):
            self._activate_target(self.targets[idx])

    def _activate_target(self, target) -> None:
        if isinstance(target, AppResult):
            self._open_app(target)
        elif isinstance(target, FileResult):
            self._open_file(target)
        elif isinstance(target, Answer):
            self.get_clipboard().set(target.value)
            self._show_text(f"Copied {target.value}")
        elif isinstance(target, WebAction):
            try:
                Gio.AppInfo.launch_default_for_uri(target.url, None)
            except GLib.Error as exc:
                self._show_text(f"Could not open the browser: {exc.message}")
            else:
                self.close()
        elif isinstance(target, SettingsPage):
            try:
                Gio.Subprocess.new(["gnome-control-center", target.panel],
                                   Gio.SubprocessFlags.NONE)
            except GLib.Error as exc:
                self._show_text(f"Could not open Settings: {exc.message}")
            else:
                self.close()
        elif target is None:
            self._ask_ai()

    def _open_file(self, file: FileResult) -> None:
        try:
            # Only a path in the verified filename catalog can arrive here.
            # Gio chooses the registered handler, not an arbitrary shell.
            if not file.path.exists() or file.path.is_symlink():
                raise FileNotFoundError(file.name)
            Gio.AppInfo.launch_default_for_uri(file.path.as_uri(), None)
        except (OSError, GLib.Error) as exc:
            self._show_text(f"Could not open {file.name}: {exc}")
        else:
            self.close()

    def _open_app(self, app: AppResult) -> None:
        self.usage.record(app.desktop_id)
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
        if provider != "builtin" and not model_sharing_allowed(provider):
            self._show_text(self._ai_off_message())
            return
        # User already opted in via setup/Settings. Do not interrupt every
        # question; the agent re-checks persisted consent before inference.
        # The question opens the chat; replies continue it (_send_chat).
        self._enter_chat()
        self.entry.set_text(query)
        self._send_chat()

    def _execute(self, operation) -> None:
        self._busy(True)
        if self.chat_mode:
            self._show_thinking()
        else:
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
        if self.chat_mode:
            self._hide_thinking()
            self.conversation.add(MECHANIC, response.message)
            self._append_bubble(MECHANIC, response.message)
            self.chat_approval.set_visible(response.pending is not None)
        else:
            self._show_text(response.message)
            self.approve_button.set_visible(response.pending is not None)
            self.cancel_button.set_visible(response.pending is not None)
        self.entry.grab_focus()
        return GLib.SOURCE_REMOVE

    def _on_approve(self, *_unused) -> None:
        action = self.pending
        self.pending = None
        self.approve_button.set_visible(False)
        self.cancel_button.set_visible(False)
        self.chat_approval.set_visible(False)
        if action:
            self._execute(lambda: self.agent.approve(action))

    def _on_decline(self, *_unused) -> None:
        self.pending = None
        self.approve_button.set_visible(False)
        self.cancel_button.set_visible(False)
        self.chat_approval.set_visible(False)
        if self.chat_mode:
            message = "Okay, I won't change anything."
            self.conversation.add(MECHANIC, message)
            self._append_bubble(MECHANIC, message)
            self.entry.grab_focus()
            return
        self._show_text("Action declined. No settings were changed.")


class AssistantApp(Adw.Application):
    def __init__(self, *, force_setup: bool = False):
        super().__init__(
            application_id="io.github.markymark5127.AIDesktop",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.force_setup = force_setup

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        # GTK and libadwaita have read these by now. Apps we launch must not
        # inherit them (a Flatpak app needs its portals for file access).
        from . import __main__ as entry
        entry.forget_portal_overrides()
        setup_action = Gio.SimpleAction.new("open-setup", None)
        setup_action.connect("activate", self._on_open_setup_action)
        self.add_action(setup_action)

    def _on_open_setup_action(self, _action, _parameter) -> None:
        launcher = next(
            (w for w in self.get_windows() if isinstance(w, AssistantWindow)),
            None,
        )
        if launcher is not None:
            launcher._open_setup()
        else:
            # Supports the action even before Spotlight has been constructed.
            self.force_setup = True
            self.activate()

    def do_command_line(self, command_line: Gio.ApplicationCommandLine) -> int:
        # Unlike a local constructor flag, this reaches the already-running
        # primary application through its D-Bus command-line handler.
        # The private "setup" positional token is supplied by __main__.py.
        args = command_line.get_arguments()
        if len(args) > 1 and args[1] == "setup":
            self.force_setup = True
        elif len(args) > 2 and args[1] == "query":
            self.initial_query = args[2]
        self.activate()
        return 0

    def _show_launcher(self) -> None:
        window = next(
            (w for w in self.get_windows() if isinstance(w, AssistantWindow)),
            None,
        )
        if window is None:
            window = AssistantWindow(self)
        else:
            window.prepare_activation()
            # Settings → Mutsu Search may have changed the look meanwhile.
            window._apply_theme(load_theme())
        window.present()
        window.entry.grab_focus()
        query, self.initial_query = getattr(self, "initial_query", ""), ""
        if query:
            window.entry.set_text(query)
            window.entry.set_position(-1)

    def open_setup_from(self, launcher: AssistantWindow) -> None:
        """Open or focus setup first; dismiss Spotlight only on success."""
        from .setup_wizard import SetupWizard

        wizard = next(
            (w for w in self.get_windows() if isinstance(w, SetupWizard)),
            None,
        )
        if wizard is None:
            wizard = SetupWizard(
                self,
                on_done=self._show_launcher,
            )
            # Closing the wizard via its traffic-light close control should
            # return to Spotlight too, not leave the session with no UI.
            wizard.connect(
                "close-request", self._on_setup_close_request, launcher
            )
        wizard.present()
        # In particular, don't hide Spotlight before __init__/present has
        # succeeded: previous code made setup launch failures look like nothing.
        launcher.hide()

    def _on_setup_close_request(
        self, _wizard: Adw.ApplicationWindow, _launcher: AssistantWindow
    ) -> bool:
        # Keep the application alive until Spotlight is shown again, even if
        # the wizard was its last currently mapped window.
        self.hold()
        GLib.idle_add(self._show_launcher_after_setup_close)
        return False

    def _show_launcher_after_setup_close(self) -> bool:
        try:
            if not any(
                isinstance(w, AssistantWindow) and w.get_visible()
                for w in self.get_windows()
            ):
                self._show_launcher()
        finally:
            self.release()
        return GLib.SOURCE_REMOVE

    def do_activate(self) -> None:
        from .onboarding import is_setup_done
        if self.force_setup or not is_setup_done():
            from .setup_wizard import SetupWizard
            wizard = next(
                (w for w in self.get_windows() if isinstance(w, SetupWizard)),
                None,
            )
            launcher = next(
                (w for w in self.get_windows() if isinstance(w, AssistantWindow)),
                None,
            )
            if launcher is not None:
                # Centralize popover close, focus guard and visible error flow.
                launcher._open_setup()
            else:
                if wizard is None:
                    wizard = SetupWizard(self, on_done=self._show_launcher)
                wizard.present()
            self.force_setup = False
            return
        # Hidden Spotlight survives focus loss, preserving in-flight Newelle
        # responses; the next Super+Space activation presents the same window.
        window = next((w for w in self.get_windows() if isinstance(w, AssistantWindow)), None)
        if window is None:
            window = AssistantWindow(self)
        else:
            window.prepare_activation()
        window.present()
        window.entry.grab_focus()
        query, self.initial_query = getattr(self, "initial_query", ""), ""
        if query:
            window.entry.set_text(query)
            window.entry.set_position(-1)
