"""GNOME/libadwaita launcher: local search is instant; AI work runs off-thread."""

from __future__ import annotations

import threading
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .agent import Agent, AgentResponse, PendingAction  # noqa: E402
from .search import AppResult, list_applications, search_applications  # noqa: E402
from .tools import run_tool  # noqa: E402


CHOICES = [
    ("Newelle (recommended)", "newelle"),
    ("Built-in (offline)", "builtin"),
    ("Local Ollama", "local"),
    ("OpenAI API", "openai"),
    ("Claude API", "anthropic"),
]


class AssistantWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application):
        super().__init__(application=application)
        self.set_title("AI Desktop")
        self.set_default_size(760, 540)
        self.agent = Agent()
        self.pending: PendingAction | None = None
        self.catalog: list[AppResult] = list_applications()
        self.matches: list[AppResult] = []
        self.busy = False

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(16)
        root.set_margin_bottom(16)
        root.set_margin_start(20)
        root.set_margin_end(20)
        self.set_content(root)

        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Ask your computer"))
        self.choice = Gtk.DropDown.new_from_strings([item[0] for item in CHOICES])
        header.pack_end(self.choice)
        root.append(header)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Search apps, or describe what you need…")
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "system-search-symbolic")
        self.entry.connect("changed", self._on_search_changed)
        self.entry.connect("activate", self._on_submit)
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._on_key)
        self.entry.add_controller(keys)
        root.append(self.entry)

        self.results = Gtk.ListBox()
        self.results.add_css_class("boxed-list")
        self.results.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.results.connect("row-activated", self._on_result_activated)
        search_scroll = Gtk.ScrolledWindow()
        search_scroll.set_min_content_height(80)
        search_scroll.set_max_content_height(225)
        search_scroll.set_propagate_natural_height(True)
        search_scroll.set_child(self.results)
        self.search_scroll = search_scroll
        root.append(search_scroll)

        self.hint = Gtk.Label(label="Enter opens an app  •  Ctrl+Enter asks AI  •  Esc closes")
        self.hint.set_xalign(0)
        self.hint.add_css_class("dim-label")
        root.append(self.hint)

        self.go = Gtk.Button(label="Ask assistant")
        self.go.add_css_class("suggested-action")
        self.go.connect("clicked", lambda *_: self._ask_ai())
        root.append(self.go)

        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        self.output = Gtk.TextView()
        self.output.set_editable(False)
        self.output.set_cursor_visible(False)
        self.output.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.output.set_top_margin(12)
        self.output.set_left_margin(12)
        self.output.set_right_margin(12)
        self.output.set_bottom_margin(12)
        scroller.set_child(self.output)
        root.append(scroller)
        self._show_text("Search installed applications instantly, or ask the assistant to diagnose a problem.\nRead-only checks work without AI or internet access.")

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.approve_button = Gtk.Button(label="Approve action")
        self.approve_button.add_css_class("suggested-action")
        self.approve_button.set_visible(False)
        self.approve_button.connect("clicked", self._on_approve)
        actions.append(self.approve_button)
        self.cancel_button = Gtk.Button(label="Decline")
        self.cancel_button.set_visible(False)
        self.cancel_button.connect("clicked", self._on_decline)
        actions.append(self.cancel_button)
        root.append(actions)
        self._update_results()
        self.entry.grab_focus()

    def _show_text(self, text: str) -> None:
        self.output.get_buffer().set_text(text)

    def _provider(self) -> str:
        return CHOICES[self.choice.get_selected()][1]

    def _busy(self, busy: bool) -> None:
        self.busy = busy
        self.go.set_sensitive(not busy)
        self.entry.set_sensitive(not busy)
        self.choice.set_sensitive(not busy)
        self.approve_button.set_sensitive(not busy)

    def _on_search_changed(self, *_unused) -> None:
        self._update_results()

    def _update_results(self) -> None:
        query = self.entry.get_text().strip()
        if query.lower().startswith(("open ", "launch ")):
            query = query.split(" ", 1)[1]
        if query.lower().startswith("ask ") or len(query.split()) > 4 or "?" in query:
            self.matches = []
        else:
            self.matches = search_applications(query, apps=self.catalog)
        while child := self.results.get_row_at_index(0):
            self.results.remove(child)
        for app in self.matches:
            row = Gtk.ListBoxRow()
            content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            content.set_margin_top(9)
            content.set_margin_bottom(9)
            content.set_margin_start(10)
            content.set_margin_end(10)
            image = Gtk.Image.new_from_icon_name(app.icon)
            image.set_pixel_size(26)
            content.append(image)
            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name = Gtk.Label(label=app.name, xalign=0)
            labels.append(name)
            if app.description:
                subtitle = Gtk.Label(label=app.description[:110], xalign=0)
                subtitle.add_css_class("dim-label")
                labels.append(subtitle)
            content.append(labels)
            row.set_child(content)
            self.results.append(row)
        self.search_scroll.set_visible(bool(self.matches))
        if self.matches:
            self.results.select_row(self.results.get_row_at_index(0))

    def _on_key(self, _controller, keyval, _keycode, state) -> bool:
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and state & Gdk.ModifierType.CONTROL_MASK:
            self._ask_ai()
            return True
        if keyval in (Gdk.KEY_Down, Gdk.KEY_Up) and self.matches:
            current = self.results.get_selected_row()
            index = current.get_index() if current else 0
            delta = 1 if keyval == Gdk.KEY_Down else -1
            new_index = max(0, min(index + delta, len(self.matches) - 1))
            self.results.select_row(self.results.get_row_at_index(new_index))
            return True
        return False

    def _on_submit(self, *_unused) -> None:
        text = self.entry.get_text().strip()
        if not text:
            return
        if self.matches and not text.lower().startswith("ask "):
            selected = self.results.get_selected_row()
            index = selected.get_index() if selected else 0
            self._open_app(self.matches[index])
        else:
            self._ask_ai()

    def _on_result_activated(self, _list_box, row) -> None:
        index = row.get_index()
        if 0 <= index < len(self.matches):
            self._open_app(self.matches[index])

    def _open_app(self, app: AppResult) -> None:
        # Activating the search result is itself an explicit user launch request.
        self.pending = None
        self.approve_button.set_visible(False)
        self.cancel_button.set_visible(False)
        self._execute(lambda: AgentResponse(run_tool("launch_application", {"desktop_id": app.desktop_id})))

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
        self.approve_button.set_visible(False)
        self.cancel_button.set_visible(False)
        if provider in ("newelle", "openai", "anthropic"):
            dialog = Gtk.MessageDialog(
                transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.NONE,
                text="Allow the selected model to receive this request?",
            )
            dialog.format_secondary_text(
                "Newelle may use a local or cloud model. Your prompt and diagnostic "
                "results can leave this computer depending on the configured provider. "
                "Do not continue with sensitive information."
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

        def worker() -> None:
            try:
                response = operation()
            except Exception as exc:
                response = AgentResponse(
                    f"Request failed ({type(exc).__name__}). "
                    "Check application availability or provider settings."
                )
            GLib.idle_add(self._on_result, response)

        threading.Thread(target=worker, daemon=True).start()

    def _on_result(self, response: AgentResponse) -> bool:
        self._busy(False)
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
        self._show_text("Action declined. No change was made.")


class AssistantApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="io.github.markymark5127.AIDesktop",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self) -> None:
        window = self.props.active_window
        if not window:
            window = AssistantWindow(self)
        window.present()
        window.entry.grab_focus()
