import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from aidesktop.spotlight import (
    UsageStore, calculate, convert_units, instant_answer, parse_content_results,
    search_settings, web_actions,
)
from aidesktop.onboarding import load_preferences, save_preferences


class CalculatorTest(unittest.TestCase):
    def test_arithmetic(self):
        for query, value in [("2+2", "4"), ("12*(3+4)", "84"), ("15% of 80", "12"),
                             ("sqrt(16)+2^3", "12"), ("2,500 * 3", "7500"),
                             ("what is 6*7?", "42"), ("10/4", "2.5"), ("50%", "0.5")]:
            self.assertEqual(calculate(query).value, value, query)

    def test_not_a_calculation(self):
        for query in ("firefox", "1.5", "e", "windows 11", "top 10", "gta5", "10/0",
                      "9**99999", "__import__('os')", "open(1)"):
            self.assertIsNone(calculate(query), query)


class ConversionTest(unittest.TestCase):
    def test_units(self):
        self.assertEqual(convert_units("5 km in miles").value, "3.10686")
        self.assertEqual(convert_units("72 f to c").value, "22.22")
        self.assertEqual(convert_units("0 c in f").value, "32")
        self.assertEqual(convert_units("2 gb in mb").value, "2000")
        self.assertEqual(convert_units("1 gib to mib").value, "1024")
        self.assertEqual(convert_units("3 cups to ml").value, "709.765")
        self.assertIsNone(convert_units("5 km in kg"), "different kinds of unit")
        self.assertIsNone(convert_units("5 apples in pears"))

    def test_instant_answer_prefers_conversion(self):
        self.assertIn("miles", instant_answer("10 km to miles").title)


class WebTest(unittest.TestCase):
    def test_typed_address_opens_site(self):
        actions = web_actions("github.com/markymark5127")
        self.assertEqual(actions[0].url, "https://github.com/markymark5127")
        self.assertIn("duckduckgo.com", actions[1].url)

    def test_search_uses_chosen_engine(self):
        (action,) = web_actions("best pizza nyc", "google")
        self.assertEqual(action.url, "https://www.google.com/search?q=best+pizza+nyc")
        self.assertEqual(web_actions(""), [])
        self.assertEqual(len(web_actions("3.14")), 1, "a number is not a website")

    def test_engine_preference(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
                self.assertEqual(load_preferences()["search_engine"], "duckduckgo")
                save_preferences(search_engine="brave")
                self.assertEqual(load_preferences()["search_engine"], "brave")
                save_preferences(search_engine="evil")
                self.assertEqual(load_preferences()["search_engine"], "duckduckgo")


class SettingsSearchTest(unittest.TestCase):
    def test_pages(self):
        self.assertEqual([p.panel for p in search_settings("wifi")], ["wifi"])
        self.assertEqual(search_settings("blue")[0].panel, "bluetooth")
        self.assertEqual(search_settings("dark mode")[0].panel, "background")
        self.assertEqual(search_settings("wi"), [], "too short")


class UsageTest(unittest.TestCase):
    def test_frequency_and_time_of_day(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "usage.json"
            store = UsageStore(path)
            now = time.mktime((2026, 11, 7, 9, 0, 0, 0, 0, -1))
            for day in range(5):
                store.record("steam.desktop", now - day * 86400 - 12 * 3600)  # evenings
                store.record("org.gnome.TextEditor.desktop", now - day * 86400)  # mornings
            store.record("steam.desktop", now - 3600 * 12)
            reloaded = UsageStore(path)
            self.assertEqual(reloaded.suggestions(
                ["steam.desktop", "org.gnome.TextEditor.desktop", "never.desktop"], now=now)[0],
                "org.gnome.TextEditor.desktop", "the app you use around now comes first")
            self.assertNotIn("never.desktop", reloaded.suggestions(["never.desktop"], now=now))
            self.assertEqual(oct(path.stat().st_mode & 0o777), "0o600")

    def test_corrupt_file_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "usage.json"
            path.write_text("{nope")
            self.assertEqual(UsageStore(path).events, {})


class ContentSearchTest(unittest.TestCase):
    def test_parser_keeps_visible_home_files(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / "Documents").mkdir()
            doc = home / "Documents" / "trip plan.odt"
            doc.write_text("x")
            hidden = home / ".cache" / "x.txt"
            hidden.parent.mkdir()
            hidden.write_text("x")
            output = (f"Results:\n  file://{home}/Documents/trip%20plan.odt\n    ...snippet...\n"
                      f"  file://{hidden}\n  file:///etc/passwd\n  file://{home}/gone.txt\n")
            self.assertEqual(parse_content_results(output, home), [doc])


if __name__ == "__main__":
    unittest.main()
