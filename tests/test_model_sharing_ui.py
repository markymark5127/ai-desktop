"""Ensure GUI privacy flow stays silent per question and opt-in driven.

Static AST inspection is intentional: our CI can run without GTK installed.
Behavioral persistence and backend denial are tested in other modules.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _method(tree: ast.AST, cls: str, method: str) -> ast.FunctionDef:
    klass = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == cls
    )
    return next(
        node for node in klass.body
        if isinstance(node, ast.FunctionDef) and node.name == method
    )


class ModelSharingUiTests(unittest.TestCase):
    def test_ask_ai_does_not_open_modal_privacy_dialog(self):
        tree = ast.parse((ROOT / "src/aidesktop/ui.py").read_text())
        ask = _method(tree, "AssistantWindow", "_ask_ai")
        names = [
            node.func.attr for node in ast.walk(ask)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        ]
        self.assertNotIn("MessageDialog", names)
        self.assertIn("model_sharing_allowed", [
            node.func.id for node in ast.walk(ask)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ])

    def test_wizard_has_its_own_checkbox_and_search_has_none(self):
        """The wizard asks; Search itself keeps no settings controls (they
        are in Settings → Mutsu Search, through aidesktop.search_settings)."""
        def checkboxes(path, cls, method):
            node = _method(ast.parse((ROOT / path).read_text()), cls, method)
            return [n for n in ast.walk(node) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute) and n.func.attr == "CheckButton"]
        self.assertGreaterEqual(len(checkboxes("src/aidesktop/setup_wizard.py", "SetupWizard", "_model")), 1)
        self.assertEqual(checkboxes("src/aidesktop/ui.py", "AssistantWindow", "__init__"), [])
        ui = (ROOT / "src/aidesktop/ui.py").read_text()
        self.assertNotIn("Gtk.Popover()", ui)
        self.assertIn('"gnome-control-center", "mutsu-search"', ui)

if __name__ == "__main__":
    unittest.main()
