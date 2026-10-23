"""Setup navigation regression checks that run without GTK in CI.

A GTK/Wayland popover can trigger focus-loss events while its button is
handling a click. The launcher must not hide itself before a separate
wizard is created/presented, otherwise a failure leaves no visible UI.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


FILE = Path(__file__).resolve().parents[1] / "src" / "aidesktop" / "ui.py"


def method_source(class_name: str, method_name: str) -> str:
    source = FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    cls = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    method = next(
        node for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )
    return ast.get_source_segment(source, method) or ""


class SetupNavigationTests(unittest.TestCase):
    def test_setup_button_defers_navigation_until_popover_closes(self):
        callback = method_source("AssistantWindow", "_open_setup")
        self.assertIn("self.settings.popdown()", callback)
        self.assertIn("GLib.idle_add(self._present_setup)", callback)
        self.assertNotIn("self.hide()", callback)

    def test_restart_dev_script_only_targets_aidesktop_module(self):
        script = (
            FILE.parents[2] / "scripts" / "restart-dev.sh"
        ).read_text(encoding="utf-8")
        self.assertIn('pgrep -u "$(id -u)" -f "$pattern"', script)
        self.assertIn("aidesktop([[:space:]]|$)", script)
        self.assertIn('exec bash "$repo_dir/scripts/run-dev.sh" "$@"', script)
        self.assertNotIn("pkill -9", script)
        self.assertNotIn("Newelle --", script)

    def test_setup_button_activates_application_action(self):
        constructor = method_source("AssistantWindow", "__init__")
        self.assertIn('self.setup_button.set_action_name("app.open-setup")', constructor)
        startup = method_source("AssistantApp", "do_startup")
        self.assertIn('Gio.SimpleAction.new("open-setup", None)', startup)
        self.assertIn("self.add_action(setup_action)", startup)
        action = method_source("AssistantApp", "_on_open_setup_action")
        self.assertIn("launcher._open_setup()", action)

    def test_setup_command_line_is_forwarded_to_existing_app(self):
        constructor = method_source("AssistantApp", "__init__")
        self.assertIn("Gio.ApplicationFlags.HANDLES_COMMAND_LINE", constructor)
        forwarded = method_source("AssistantApp", "do_command_line")
        self.assertIn('args[1] == "setup"', forwarded)
        self.assertIn("self.force_setup = True", forwarded)
        self.assertIn("self.activate()", forwarded)
        main = (
            FILE.parent / "__main__.py"
        ).read_text(encoding="utf-8")
        self.assertIn('["ai-desktop", "setup"] if args.setup else ["ai-desktop"]', main)
        self.assertIn("app.run(internal_argv)", main)
        self.assertNotIn("app.run(None)", main)

    def test_wizard_is_presented_before_spotlight_is_hidden(self):
        navigation = method_source("AssistantApp", "open_setup_from")
        self.assertIn("wizard = SetupWizard(", navigation)
        self.assertIn("wizard.present()", navigation)
        self.assertIn("launcher.hide()", navigation)
        self.assertLess(
            navigation.index("wizard.present()"),
            navigation.index("launcher.hide()"),
        )

    def test_setup_error_is_visible_instead_of_silent(self):
        navigation = method_source("AssistantWindow", "_present_setup")
        self.assertIn("except Exception as exc:", navigation)
        self.assertIn("traceback.print_exc()", navigation)
        self.assertIn("self._show_text(", navigation)
        self.assertIn("self.present()", navigation)
        self.assertIn("self._opening_setup = False", navigation)

    def test_setup_focus_change_cannot_hide_spotlight_mid_transition(self):
        for method in ("_on_active_changed", "_dismiss_if_unfocused"):
            with self.subTest(method=method):
                src = method_source("AssistantWindow", method)
                self.assertIn("if self._opening_setup:", src)

    def test_closing_wizard_can_reopen_existing_launcher(self):
        nav = method_source("AssistantApp", "open_setup_from")
        close = method_source("AssistantApp", "_on_setup_close_request")
        show = method_source("AssistantApp", "_show_launcher")
        self.assertIn('"close-request"', nav)
        self.assertIn("GLib.idle_add(", close)
        self.assertIn("self.get_windows()", show)


if __name__ == "__main__":
    unittest.main()
