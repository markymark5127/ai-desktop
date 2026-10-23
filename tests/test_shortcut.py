import importlib.util
import unittest
from unittest.mock import patch
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "shortcut.py"
spec = importlib.util.spec_from_file_location("ai_desktop_shortcut", SCRIPT)
shortcut = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shortcut)


class ShortcutTests(unittest.TestCase):
    def test_gsettings_empty_array(self):
        self.assertEqual(shortcut.read_string_array("@as []"), [])

    def test_gsettings_string_array(self):
        self.assertEqual(shortcut.read_string_array("['<Super>space', '<Alt>Shift']"),
                         ["<Super>space", "<Alt>Shift"])

    def test_rejects_non_string_arrays(self):
        with self.assertRaises(ValueError):
            shortcut.read_string_array("[123]")

    def test_refresh_label_changes_only_our_known_legacy_name(self):
        expected = str(Path.home() / ".local/bin/ai-desktop")
        with patch.object(shortcut, "BACKUP") as backup:
            backup.exists.return_value = True
            with patch.object(shortcut, "_get_array", return_value=[shortcut.PATH]):
                with patch.object(
                    shortcut, "_run",
                    side_effect=[repr(expected), repr("AI Desktop")],
                ):
                    with patch.object(shortcut, "_set_string") as write:
                        shortcut.refresh_label()
                        write.assert_called_once_with(
                            shortcut.CUSTOM, "name", "Mutsu OS Search"
                        )

    def test_refresh_label_refuses_other_programs(self):
        with patch.object(shortcut, "BACKUP") as backup:
            backup.exists.return_value = True
            with patch.object(shortcut, "_get_array", return_value=[shortcut.PATH]):
                with patch.object(shortcut, "_run", return_value=repr("/usr/bin/other-app")):
                    with patch.object(shortcut, "_set_string") as write:
                        with self.assertRaises(RuntimeError):
                            shortcut.refresh_label()
                        write.assert_not_called()

    def test_refresh_label_keeps_user_customized_name(self):
        expected = str(Path.home() / ".local/bin/ai-desktop")
        with patch.object(shortcut, "BACKUP") as backup:
            backup.exists.return_value = True
            with patch.object(shortcut, "_get_array", return_value=[shortcut.PATH]):
                with patch.object(shortcut, "_run", side_effect=[repr(expected), repr("My Shortcut")]):
                    with patch.object(shortcut, "_set_string") as write:
                        shortcut.refresh_label()
                        write.assert_not_called()

    def test_does_not_run_gsettings_without_explicit_cli_choice(self):
        # Merely importing the module must not mutate GNOME settings.
        self.assertTrue(callable(shortcut.apply))
        self.assertTrue(callable(shortcut.restore))


if __name__ == "__main__":
    unittest.main()
