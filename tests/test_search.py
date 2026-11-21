import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aidesktop.search import (
    AppResult, applications_stamp, list_applications, resolve_app_id, search_applications,
)


class SearchTests(unittest.TestCase):
    def test_friendly_search_and_ranking(self):
        apps = [AppResult('org.gnome.Settings.desktop', 'Settings'), AppResult('steam.desktop', 'Steam'), AppResult('steamtools.desktop', 'Steam Tools')]
        self.assertEqual([a.name for a in search_applications('steam', apps=apps)], ['Steam', 'Steam Tools'])
        self.assertEqual(search_applications('not-there', apps=apps), [])

    def test_resolve_only_known_ids(self):
        apps = [AppResult('org.gnome.Calculator.desktop', 'Calculator')]
        self.assertTrue(resolve_app_id('org.gnome.Calculator.desktop', apps))
        self.assertFalse(resolve_app_id('bash.desktop', apps))

    def test_parsing_hides_system_entries_and_respects_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            user = Path(tmp) / 'user'
            system = Path(tmp) / 'system'
            user.mkdir()
            system.mkdir()
            (user / 'steam.desktop').write_text('[Desktop Entry]\nType=Application\nName=Steam from user\n', encoding='utf-8')
            (system / 'steam.desktop').write_text('[Desktop Entry]\nType=Application\nName=Steam from system\n', encoding='utf-8')
            (user / 'hidden.desktop').write_text('[Desktop Entry]\nType=Application\nName=Hidden\nNoDisplay=true\n', encoding='utf-8')
            (user / 'gnome.desktop').write_text('[Desktop Entry]\nType=Application\nName=GNOME only\nOnlyShowIn=GNOME;\n', encoding='utf-8')
            with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'GNOME'}):
                apps = list_applications([user, system])
            self.assertEqual([a.name for a in apps], ['GNOME only', 'Steam from user'])


if __name__ == '__main__':
    unittest.main()


class ApplicationsStampTests(unittest.TestCase):
    def test_changes_when_an_app_is_installed_or_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            apps = Path(tmp, "applications")
            apps.mkdir()
            missing = Path(tmp, "missing")
            before = applications_stamp([apps, missing])
            self.assertEqual(before[1], None)
            self.assertEqual(applications_stamp([apps, missing]), before)
            desktop = apps / "new.desktop"
            desktop.write_text("[Desktop Entry]\nType=Application\nName=New\n")
            os.utime(apps, ns=(before[0] + 10**9, before[0] + 10**9))
            installed = applications_stamp([apps, missing])
            self.assertNotEqual(installed, before)
            desktop.unlink()
            os.utime(apps, ns=(before[0] + 2 * 10**9, before[0] + 2 * 10**9))
            self.assertNotEqual(applications_stamp([apps, missing]), installed)

