import unittest

from aidesktop.search import AppResult
from aidesktop.search_routing import route_query, should_hide_on_focus_loss


class SpotlightRoutingTests(unittest.TestCase):
    def setUp(self):
        self.apps = [
            AppResult("steam.desktop", "Steam", "Play PC games"),
            AppResult("org.gnome.Nautilus.desktop", "Files", "File manager"),
            AppResult("org.gnome.Settings.desktop", "Settings", "Change preferences"),
        ]

    def test_plain_app_name_prefers_installed_app_and_offers_ai(self):
        result = route_query("Steam", self.apps)
        self.assertEqual(result.apps[0].name, "Steam")
        self.assertTrue(result.offer_ai)

    def test_no_match_offers_ai_without_calling_it(self):
        result = route_query("why can't my controller connect", self.apps)
        self.assertEqual(result.apps, ())
        self.assertTrue(result.offer_ai)
        self.assertEqual(result.query, "why can't my controller connect")

    def test_natural_language_does_not_accidentally_launch_apps(self):
        result = route_query("How do I open Steam?", self.apps)
        self.assertEqual(result.apps, ())
        self.assertTrue(result.offer_ai)

    def test_explicit_open_uses_local_matches(self):
        result = route_query("open Files", self.apps)
        self.assertEqual(result.apps[0].name, "Files")

    def test_empty_query_shows_no_results(self):
        result = route_query("   ", self.apps)
        self.assertEqual(result.apps, ())
        self.assertFalse(result.offer_ai)

    def test_explicit_ask_skips_local_results(self):
        result = route_query("ask Steam", self.apps)
        self.assertEqual(result.apps, ())
        self.assertEqual(result.query, "Steam")

    def test_focus_loss_requires_real_prior_activation(self):
        args = dict(activated_once=True, is_active=False, is_visible=True,
                    modal_dialog=False, settings_open=False)
        self.assertTrue(should_hide_on_focus_loss(**args))
        for key, value in (
            ("activated_once", False),
            ("is_active", True),
            ("is_visible", False),
            ("modal_dialog", True),
            ("settings_open", True),
        ):
            with self.subTest(key=key):
                self.assertFalse(should_hide_on_focus_loss(**{**args, key: value}))


if __name__ == "__main__":
    unittest.main()
