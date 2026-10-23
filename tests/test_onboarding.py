import json
import os
import stat
import tempfile
import unittest
from unittest.mock import patch

from aidesktop.onboarding import (
    DEFAULTS, LEARNING_STYLES, get_learning_style, helper_intro, is_setup_done,
    load_preferences, mark_setup_done, preferences_path, save_preferences,
    model_sharing_allowed, set_model_sharing_allowed,
)


class OnboardingTests(unittest.TestCase):
    def test_defaults_no_setup_without_writing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
                self.assertFalse(is_setup_done())
                self.assertEqual(load_preferences(), DEFAULTS)
                self.assertFalse(preferences_path().exists())

    def test_persist_choice_and_completion_privately(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
                save_preferences(learning_style="learn", phone="iphone")
                self.assertEqual(get_learning_style(), "learn")
                self.assertEqual(load_preferences()["phone"], "iphone")
                self.assertEqual(stat.S_IMODE(preferences_path().stat().st_mode), 0o600)
                mark_setup_done()
                self.assertTrue(is_setup_done())
                self.assertEqual(load_preferences()["status"], "completed")

    def test_model_sharing_defaults_off_and_can_be_revoked(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
                self.assertFalse(model_sharing_allowed())
                set_model_sharing_allowed(True)
                self.assertTrue(model_sharing_allowed())
                self.assertIs(load_preferences()["model_sharing"], True)
                set_model_sharing_allowed(False)
                self.assertFalse(model_sharing_allowed())
                self.assertEqual(
                    stat.S_IMODE(preferences_path().stat().st_mode), 0o600
                )
                with self.assertRaises(ValueError):
                    set_model_sharing_allowed("yes")

    def test_older_preference_file_stays_valid_without_silent_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
                p = preferences_path()
                p.parent.mkdir(parents=True)
                p.write_text(
                    '{"status":"completed","phone":"iphone","learning_style":"learn"}'
                )
                self.assertFalse(model_sharing_allowed())
                self.assertTrue(is_setup_done())
                self.assertEqual(load_preferences()["learning_style"], "learn")

    def test_corrupt_consent_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
                p = preferences_path()
                p.parent.mkdir(parents=True)
                p.write_text('{"model_sharing":"true"}')
                self.assertFalse(model_sharing_allowed())

    def test_skipping_is_reopenable(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
                mark_setup_done(skipped=True)
                self.assertEqual(load_preferences()["status"], "skipped")
                self.assertTrue(is_setup_done())

    def test_invalid_options_do_not_mutate_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
                save_preferences(learning_style="guided")
                before = preferences_path().read_bytes()
                for attempt in (
                    {"learning_style": "danger"}, {"status": "granted"},
                    {"unknown": "value"}, {"phone": "windows"},
                ):
                    with self.subTest(attempt=attempt):
                        with self.assertRaises(ValueError):
                            save_preferences(**attempt)
                        self.assertEqual(preferences_path().read_bytes(), before)

    def test_corrupted_file_defaults_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
                p = preferences_path()
                p.parent.mkdir(parents=True)
                p.write_text('{"status":"unknown"}', encoding="utf-8")
                self.assertEqual(load_preferences(), DEFAULTS)

    def test_learning_levels_do_not_modify_authorizations(self):
        self.assertEqual([key for _, key in LEARNING_STYLES], ["simple", "guided", "learn"])
        self.assertIn("changing settings", helper_intro("guided"))
        self.assertIn("Mac comparisons", helper_intro("learn"))
        with self.assertRaises(ValueError):
            helper_intro("root")


if __name__ == "__main__":
    unittest.main()
