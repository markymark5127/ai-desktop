import json
import os
import stat
import tempfile
import unittest
from unittest.mock import patch

from aidesktop.keyboard_profiles import (
    KeyboardError, apply_profile_layout, backup_path, get_profile,
    parse_sources, preference_path, prepend_layout, restore_previous_layout,
    set_profile, shortcut_label, super_label,
)


class KeyboardProfileTests(unittest.TestCase):
    def test_mac_and_standard_shortcut_labels(self):
        self.assertEqual(super_label("mac"), "⌘ Command")
        self.assertEqual(shortcut_label("mac"), "⌘ + Space")
        self.assertEqual(super_label("standard"), "Win / Super")
        self.assertEqual(shortcut_label("standard"), "Win + Space")

    def test_profile_persists_privately(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": root}):
                self.assertEqual(get_profile(), "standard")
                set_profile("mac")
                self.assertEqual(get_profile(), "mac")
                self.assertEqual(stat.S_IMODE(preference_path().stat().st_mode), 0o600)
                with self.assertRaises(ValueError):
                    set_profile("unknown")
                self.assertEqual(get_profile(), "mac")

    def test_preserve_other_input_sources(self):
        sources = [("xkb", "us"), ("xkb", "de"), ("ibus", "mozc-jp")]
        self.assertEqual(prepend_layout("mac", sources), [
            ("xkb", "us+mac"), *sources
        ])
        self.assertEqual(prepend_layout("standard", sources), sources)

    def test_parse_gvariant_layouts_safely(self):
        self.assertEqual(parse_sources("@a(ss) []"), [])
        self.assertEqual(parse_sources("[('xkb', 'us'), ('xkb', 'de')]"),
                         [("xkb", "us"), ("xkb", "de")])
        for invalid in ["__import__('os').system('true')", "[123]", "('xkb', 'us')"]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(KeyboardError):
                    parse_sources(invalid)

    def test_apply_and_restore_preserve_originals(self):
        old = [("xkb", "us"), ("xkb", "de")]
        writes = []
        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, {"XDG_STATE_HOME": root}):
                with patch("aidesktop.keyboard_profiles.read_sources", return_value=old):
                    with patch("aidesktop.keyboard_profiles.write_sources", side_effect=lambda v: writes.append(v)):
                        self.assertIn("us+mac", apply_profile_layout("mac"))
                        self.assertTrue(backup_path().exists())
                        self.assertEqual(stat.S_IMODE(backup_path().stat().st_mode), 0o600)
                        self.assertEqual(writes[0], [("xkb", "us+mac"), *old])
                        saved = json.loads(backup_path().read_text())
                        self.assertEqual(saved["sources"], [list(x) for x in old])
                        self.assertIn("Restored", restore_previous_layout())
                        self.assertEqual(writes[1], old)
                        self.assertFalse(backup_path().exists())

    def test_no_change_if_already_active(self):
        with patch("aidesktop.keyboard_profiles.read_sources", return_value=[("xkb", "us+mac")]):
            with patch("aidesktop.keyboard_profiles.write_sources") as write:
                self.assertIn("already first", apply_profile_layout("mac"))
                write.assert_not_called()

    def test_restore_without_backup(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, {"XDG_STATE_HOME": root}):
                with self.assertRaises(KeyboardError):
                    restore_previous_layout()


if __name__ == "__main__":
    unittest.main()
