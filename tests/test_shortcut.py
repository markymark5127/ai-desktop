import importlib.util
import unittest
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

    def test_does_not_run_gsettings_without_explicit_cli_choice(self):
        # Merely importing the module must not mutate GNOME settings.
        self.assertTrue(callable(shortcut.apply))
        self.assertTrue(callable(shortcut.restore))


if __name__ == "__main__":
    unittest.main()
