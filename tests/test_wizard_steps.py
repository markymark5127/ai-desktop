import tempfile
import unittest
from pathlib import Path

from aidesktop import wizard_steps
import ast

_SRC = Path(__file__).resolve().parents[1] / "src/aidesktop/setup_wizard.py"
STEPS = next(ast.literal_eval(node.value) for node in ast.parse(_SRC.read_text()).body
             if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "STEPS")


class Result:
    def __init__(self, out):
        self.stdout = out


class WizardStepTests(unittest.TestCase):
    def test_step_order(self):
        self.assertEqual(STEPS, ("Welcome", "Get online", "Look and keyboard", "Your phone",
                                 "AI and privacy", "Backups", "You are ready"))

    def test_wifi_name_from_nmcli(self):
        out = "no:Neighbours\\:5G\nyes:Home\\:Wi-Fi\n"
        with unittest.mock.patch("shutil.which", return_value="/usr/bin/nmcli"):
            self.assertEqual(wizard_steps.wifi_name(lambda *a, **k: Result(out)), "Home:Wi-Fi")
            self.assertIsNone(wizard_steps.wifi_name(lambda *a, **k: Result("no:Other\n")))

    def test_connection_summary(self):
        self.assertEqual(wizard_steps.connection_summary(True, "Home"), "Connected to Home.")
        self.assertIn("Not connected", wizard_steps.connection_summary(False, None))

    def test_backup_app_detection(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(wizard_steps.backup_app_installed([d]))
            Path(d, "org.gnome.DejaDup.desktop").touch()
            self.assertTrue(wizard_steps.backup_app_installed([d]))

    def test_alpha_and_privacy_copy(self):
        self.assertIn("developer alpha", wizard_steps.ALPHA_NOTICE)
        self.assertTrue(any("on this computer" in t for t, _ in wizard_steps.PRIVACY_POINTS))


import unittest.mock  # noqa: E402

if __name__ == "__main__":
    unittest.main()
