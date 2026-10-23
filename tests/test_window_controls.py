import json
import os
import tempfile
import unittest
from unittest.mock import patch

from aidesktop.window_controls import (
    MAC_LAYOUT, WindowLayoutError, apply_mac_layout, backup_path,
    current_layout, restore_previous_layout,
)


class WindowControlsTests(unittest.TestCase):
    def test_gsettings_layout_parsed_without_eval(self):
        with patch("aidesktop.window_controls._gsettings", return_value="'minimize,maximize,close:'"):
            self.assertEqual(current_layout(), "minimize,maximize,close:")
        with patch("aidesktop.window_controls._gsettings", return_value="__import__('os').system('true')"):
            with self.assertRaises(WindowLayoutError):
                current_layout()

    def test_apply_then_restore_original_layout(self):
        state = {"value": "appmenu:minimize,maximize,close"}
        def fake_settings(action, schema, key, *rest):
            if action == "get":
                return repr(state["value"])
            self.assertEqual(action, "set")
            state["value"] = rest[0]
            return ""

        with tempfile.TemporaryDirectory() as path:
            with patch.dict(os.environ, {"XDG_STATE_HOME": path}):
                with patch("aidesktop.window_controls._gsettings", side_effect=fake_settings):
                    self.assertIn("now on the left", apply_mac_layout())
                    self.assertEqual(state["value"], MAC_LAYOUT)
                    self.assertTrue(backup_path().exists())
                    self.assertEqual(json.loads(backup_path().read_text())["value"],
                                     "appmenu:minimize,maximize,close")
                    self.assertIn("restored", restore_previous_layout())
                    self.assertEqual(state["value"], "appmenu:minimize,maximize,close")
                    self.assertFalse(backup_path().exists())

    def test_already_mac_does_not_create_backup(self):
        with tempfile.TemporaryDirectory() as path:
            with patch.dict(os.environ, {"XDG_STATE_HOME": path}):
                with patch("aidesktop.window_controls.current_layout", return_value=MAC_LAYOUT):
                    self.assertIn("already", apply_mac_layout())
                    self.assertFalse(backup_path().exists())

    def test_corrupt_backup_never_modifies_gnome(self):
        with tempfile.TemporaryDirectory() as path:
            with patch.dict(os.environ, {"XDG_STATE_HOME": path}):
                backup_path().parent.mkdir(parents=True)
                backup_path().write_text('{"schema": "not gnome", "key":"button-layout", "value":"x"}')
                with patch("aidesktop.window_controls._gsettings") as settings:
                    with self.assertRaises(WindowLayoutError):
                        restore_previous_layout()
                    settings.assert_not_called()


if __name__ == "__main__":
    unittest.main()
