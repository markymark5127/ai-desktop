import json
import os
import tempfile
import unittest
from unittest.mock import patch

from aidesktop.dock import (
    DockError, MANAGED_KEYS, apply_dock, backup_path, restore_dock,
    settings_for, dock_status,
)


class DockTests(unittest.TestCase):
    def test_defaults_are_persistent_mac_dock_with_app_grid(self):
        options = settings_for("BOTTOM", True)
        self.assertEqual(options["dock-position"], "'BOTTOM'")
        self.assertEqual(options["dock-fixed"], "true")
        self.assertEqual(options["autohide"], "false")
        self.assertEqual(options["show-show-apps-button"], "true")
        self.assertEqual(options["show-apps-at-top"], "true")
        self.assertEqual(options["extend-height"], "false")

    def test_all_positions_supported_without_changes_to_overview(self):
        for position in ("BOTTOM", "LEFT", "RIGHT", "TOP"):
            self.assertEqual(settings_for(position, True)["dock-position"], f"'{position}'")
        with self.assertRaises(DockError):
            settings_for("OVERLAY", True)

    def test_missing_extension_never_changes_settings(self):
        with patch("aidesktop.dock._schema_available", return_value=False):
            with patch("aidesktop.dock._set") as setter:
                with self.assertRaises(DockError):
                    apply_dock()
                setter.assert_not_called()

    def test_reversible_apply_and_restore(self):
        originals = {key: "'LEFT'" if key == "dock-position" else "false" for key in MANAGED_KEYS}
        writes = []
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_STATE_HOME": tmp}):
                with patch("aidesktop.dock._schema_available", return_value=True):
                    with patch("aidesktop.dock._enabled_extension", return_value="dash-to-dock@micxgx.gmail.com"):
                        with patch("aidesktop.dock._get", side_effect=lambda key: originals[key]):
                            with patch("aidesktop.dock._set", side_effect=lambda name, value: writes.append((name, value))):
                                self.assertIn("Bottom dock", apply_dock())
                                self.assertTrue(backup_path().exists())
                                self.assertEqual(set(json.loads(backup_path().read_text())["values"]), set(MANAGED_KEYS))
                                self.assertIn(("dock-fixed", "true"), writes)
                                writes.clear()
                                self.assertIn("restored", restore_dock())
                                self.assertEqual(dict(writes), originals)
                                self.assertFalse(backup_path().exists())

    def test_bad_backup_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_STATE_HOME": tmp}):
                backup_path().parent.mkdir()
                backup_path().write_text('{"schema":"other","values":{}}')
                with patch("aidesktop.dock._set") as setter:
                    with self.assertRaises(DockError):
                        restore_dock()
                    setter.assert_not_called()


if __name__ == "__main__":
    unittest.main()
