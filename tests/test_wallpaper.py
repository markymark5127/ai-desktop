import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aidesktop import wallpaper


class MutsuWallpaperTests(unittest.TestCase):
    def test_filename_contract_and_real_assets(self):
        self.assertEqual(wallpaper.WALLPAPER_NAMES["japandi"], "mutsu-japandi-4k.png")
        self.assertEqual(wallpaper.WALLPAPER_NAMES["cyberpunk"], "mutsu-cyberpunk-4k.png")
        for theme in wallpaper.WALLPAPER_NAMES:
            self.assertTrue(wallpaper.find_wallpaper(theme).is_file())
        with self.assertRaises(wallpaper.WallpaperError):
            wallpaper.find_wallpaper("unknown")

    def test_theme_switch_and_system_restores_original_wallpaper(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            image_a = home / "mutsu-japandi-4k.png"
            image_b = home / "mutsu-cyberpunk-4k.png"
            image_a.write_bytes(b"test")
            image_b.write_bytes(b"test")
            current = {
                "picture-uri": "file:///original-light.png",
                "picture-uri-dark": "file:///original-dark.png",
            }
            def asset(theme):
                return image_a if theme == "japandi" else image_b
            with patch.dict(os.environ, {"XDG_STATE_HOME": temp}):
                with patch.object(wallpaper.shutil, "which", return_value="/bin/gsettings"):
                    with patch.object(wallpaper, "find_wallpaper", side_effect=asset):
                        with patch.object(wallpaper, "_get", side_effect=lambda key: current[key]):
                            with patch.object(wallpaper, "_set", side_effect=lambda key, val: current.__setitem__(key, val)):
                                wallpaper.apply_theme_wallpaper("japandi")
                                self.assertEqual(current["picture-uri"], image_a.as_uri())
                                backup = wallpaper._state_path()
                                self.assertTrue(backup.is_file())
                                self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)
                                wallpaper.apply_theme_wallpaper("cyberpunk")
                                self.assertEqual(current["picture-uri-dark"], image_b.as_uri())
                                self.assertEqual(
                                    json.loads(backup.read_text())["previous"]["picture-uri"],
                                    "file:///original-light.png"
                                )
                                wallpaper.apply_theme_wallpaper("system")
                                self.assertEqual(current["picture-uri"], "file:///original-light.png")
                                self.assertEqual(current["picture-uri-dark"], "file:///original-dark.png")
                                self.assertFalse(backup.exists())

    def test_system_restoration_does_not_overwrite_manual_user_change(self):
        with tempfile.TemporaryDirectory() as temp:
            picture = Path(temp) / "mutsu-japandi-4k.png"
            picture.write_bytes(b"test")
            current = {key: "file:///original.png" for key in wallpaper.KEYS}
            with patch.dict(os.environ, {"XDG_STATE_HOME": temp}):
                with patch.object(wallpaper.shutil, "which", return_value="/bin/gsettings"):
                    with patch.object(wallpaper, "find_wallpaper", return_value=picture):
                        with patch.object(wallpaper, "_get", side_effect=lambda key: current[key]):
                            with patch.object(wallpaper, "_set", side_effect=lambda key, val: current.__setitem__(key, val)):
                                wallpaper.apply_theme_wallpaper("japandi")
                                current["picture-uri"] = "file:///manually-set.png"
                                notice = wallpaper.apply_theme_wallpaper("system")
                                self.assertIn("keeping your manually changed", notice)
                                self.assertEqual(current["picture-uri"], "file:///manually-set.png")


if __name__ == "__main__":
    unittest.main()
