"""Settings → Mutsu Search reads and writes through aidesktop.search_settings."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SearchSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {**os.environ, "XDG_CONFIG_HOME": self.tmp.name, "PYTHONPATH": str(ROOT / "src")}

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        result = subprocess.run([sys.executable, "-m", "aidesktop.search_settings", *args],
                                env=self.env, capture_output=True, text=True)
        return result.returncode, json.loads(result.stdout)

    def test_defaults(self):
        code, data = self.run_cli("get")
        self.assertEqual(code, 0)
        self.assertEqual(data["provider"], "newelle")
        self.assertTrue(data["ai_enabled"])
        self.assertFalse(data["cloud_allowed"], "cloud AI stays off until asked for")
        self.assertEqual(data["search_engine"], "duckduckgo")
        self.assertIn(["newelle", "Mutsu Mechanic (on this computer)"], data["providers"])

    def test_settings_are_saved_where_search_reads_them(self):
        self.run_cli("set", "provider", "local")
        self.run_cli("set", "search_engine", "brave")
        self.run_cli("set", "ai_enabled", "false")
        self.run_cli("set", "cloud_allowed", "true")
        _, data = self.run_cli("get")
        self.assertEqual((data["provider"], data["search_engine"]), ("local", "brave"))
        self.assertFalse(data["ai_enabled"])
        self.assertTrue(data["cloud_allowed"])
        saved = json.loads((Path(self.tmp.name) / "ai-desktop" / "onboarding.json").read_text())
        self.assertEqual(saved["provider"], "local")

    def test_cloud_provider_without_consent_says_so(self):
        _, data = self.run_cli("set", "provider", "anthropic")
        self.assertIn("cloud", data["message"].lower())

    def test_bad_values_are_refused(self):
        for args in (("set", "provider", "skynet"), ("set", "search_engine", "x"),
                     ("set", "ai_enabled", "maybe"), ("set", "nope", "1")):
            code, data = self.run_cli(*args)
            self.assertEqual(code, 1, args)
            self.assertIn("error", data)

    def test_ai_test_respects_the_switch(self):
        self.run_cli("set", "ai_enabled", "off")
        _, data = self.run_cli("test-ai")
        self.assertFalse(data["ok"])


if __name__ == "__main__":
    unittest.main()
