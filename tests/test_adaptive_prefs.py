"""Tablet mode choice in the welcome wizard (adaptive_prefs)."""

import subprocess
import unittest
from unittest import mock

from aidesktop import adaptive_prefs


class AdaptivePrefsTests(unittest.TestCase):
    def fake(self, code, out=""):
        return mock.patch.object(adaptive_prefs.subprocess, "run",
                                 return_value=subprocess.CompletedProcess([], code, out, ""))

    def test_set_and_get(self):
        with self.fake(0) as run:
            self.assertIn("Always tablet", adaptive_prefs.set_adaptive_mode("always-tablet"))
            argv = run.call_args.args[0]
            self.assertEqual(argv[-4:], ["set", adaptive_prefs.SCHEMA, "mode", "always-tablet"])
        with self.fake(0, "'automatic'\n"):
            self.assertEqual(adaptive_prefs.get_adaptive_mode(), "automatic")

    def test_unknown_mode_is_refused_without_running_anything(self):
        with self.fake(0) as run:
            self.assertIn("Unknown", adaptive_prefs.set_adaptive_mode("sideways"))
            run.assert_not_called()

    def test_missing_extension(self):
        with self.fake(1):
            self.assertIsNone(adaptive_prefs.get_adaptive_mode())
            self.assertIn("isn't available", adaptive_prefs.set_adaptive_mode("automatic"))


if __name__ == "__main__":
    unittest.main()
