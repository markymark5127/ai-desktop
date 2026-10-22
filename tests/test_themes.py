import json
import os
import stat
import tempfile
import unittest
from unittest.mock import patch

from aidesktop.themes import SCHEMES, STYLES, THEME_LABELS, config_path, load_theme, save_theme, validate_theme


class ThemeTests(unittest.TestCase):
    def test_three_themes_have_scoped_gtk_css(self):
        self.assertEqual([key for _, key in THEME_LABELS], ["system", "japandi", "cyberpunk"])
        self.assertEqual(set(STYLES), set(SCHEMES))
        self.assertEqual(STYLES["system"], "")
        for name in ("japandi", "cyberpunk"):
            self.assertIn(".ai-desktop", STYLES[name])
            self.assertIn("entry", STYLES[name])
            self.assertIn("textview", STYLES[name])
            self.assertIn("button.suggested-action", STYLES[name])

    def test_persist_and_reload_theme(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp}):
                self.assertEqual(load_theme(), "japandi")
                save_theme("cyberpunk")
                self.assertEqual(load_theme(), "cyberpunk")
                self.assertEqual(json.loads(config_path().read_text())["theme"], "cyberpunk")
                self.assertEqual(stat.S_IMODE(config_path().stat().st_mode), 0o600)
                save_theme("system")
                self.assertEqual(load_theme(), "system")

    def test_rejects_invalid_persisted_value_and_invalid_theme(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp}):
                config_path().parent.mkdir()
                config_path().write_text('{"theme":"unknown"}')
                self.assertEqual(load_theme(), "japandi")
                with self.assertRaises(ValueError):
                    save_theme("../etc/shadow")
                self.assertEqual(validate_theme("japandi"), "japandi")


if __name__ == "__main__":
    unittest.main()
