"""Regression tests for GTK4 dialog API compatibility.

The varargs C function Gtk.MessageDialog.format_secondary_text is not
available through Python GI even though it is documented in gtk4 C API.
Use its writable 'secondary-text' GObject property instead.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GtkDialogCompatibilityTests(unittest.TestCase):
    def test_remaining_setup_dialogs_use_introspectable_property(self):
        for relative, expected_dialogs in (
            ("src/aidesktop/ui.py", 0),
            ("src/aidesktop/setup_wizard.py", 3),
        ):
            with self.subTest(path=relative):
                tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
                removed_varargs_calls = [
                    node for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "format_secondary_text"
                ]
                self.assertEqual(removed_varargs_calls, [])
                supported_assignments = [
                    target
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Assign)
                    for target in node.targets
                    if isinstance(target, ast.Attribute)
                    and target.attr == "secondary_text"
                    and isinstance(target.value, ast.Attribute)
                    and target.value.attr == "props"
                ]
                self.assertEqual(len(supported_assignments), expected_dialogs)
                # The privacy modal was removed from the Spotlight launcher;
                # other user-approved GNOME setting changes keep their dialogs.


if __name__ == "__main__":
    unittest.main()
