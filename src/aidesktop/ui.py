"""Small GNOME/libadwaita window. All blocking AI operations run off the GTK thread."""

from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

from .agent import Agent, AgentResponse, PendingAction  # noqa: E402


CHOICES = [
    ("Built-in tools (offline)", "builtin"),
    ("Local AI (Ollama)", "local"),
    ("OpenAI API (cloud)", "openai"),
    ("Claude API (cloud)", "anthropic"),
]


class AssistantWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application):
        super().__init__(application=application)
        self.set_title("AI Desktop")
        self.set_default_size(720, 475)
        self.agent = Agent()
        self.pending: PendingAction | None = None

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
        self.entry.set_placeholder_text("Search, ask a question, or describe a problem…")
        self.entry.connect("activate", self._on_submit)
        root.append(self.entry)

        self.go = Gtk.Button(label="Ask")
        self.go.add_css_class("suggested-action")
        self.go.connect("clicked", self._on_submit)
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
        self._show_text(
            "Try 'my sound is not working', 'network status', or 'system info'.\n"
            "Built-in tools work without AI; choose Ollama, OpenAI, or Claude "
            "for natural-language planning."
        )

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

        self.entry.grab_focus()

    def _show_text(self, text: str) -> None:
        self.output.get_buffer().set_text(text)

    def _provider(self) -> str:
        return CHOICES[self.choice.get_selected()][1]

    def _busy(self, busy: bool) -> None:
        self.go.set_sensitive(not busy)
        self.entry.set_sensitive(not busy)
        self.choice.set_sensitive(not busy)
        self.approve_button.set_sensitive(not busy)

    def _on_submit(self, *_unused) -> None:
        query = self.entry.get_text().strip()
        if not query:
            return
        provider = self._provider()
        self.pending = None
        self.approve_button.set_visible(False)
        self.cancel_button.set_visible(False)
        if provider in ("openai", "anthropic"):
            # Consent is requested PER request. Diagnostic outputs may contain
            # names, paths or personal information and are sent to the provider.
            dialog = Gtk.MessageDialog(
                transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.NONE,
                text="Send this request and diagnostic results to a cloud AI?",
            )
            dialog.format_secondary_text(
                "The selected provider will receive your request, and any tool "
                "results used to answer it. Do not continue with sensitive logs."
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
                # Avoid echoing provider exception bodies or credentials.
                response = AgentResponse(
                    f"Request failed ({type(exc).__name__}). "
                    "Check your provider configuration and connection."
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
