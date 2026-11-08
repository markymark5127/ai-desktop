import os
import unittest
from unittest import mock

from aidesktop import __main__ as entry


class PortalEnvTests(unittest.TestCase):
    def test_overrides_are_set_then_forgotten(self):
        with mock.patch.dict(os.environ, {"GDK_DEBUG": "events"}, clear=False):
            os.environ.pop("ADW_DISABLE_PORTAL", None)
            entry._no_portal_settings()
            self.assertEqual(os.environ["ADW_DISABLE_PORTAL"], "1")
            self.assertEqual(os.environ["GDK_DEBUG"], "events,no-portals")
            entry.forget_portal_overrides()
            self.assertNotIn("ADW_DISABLE_PORTAL", os.environ)
            self.assertEqual(os.environ["GDK_DEBUG"], "events", "apps we launch get the user's own env")


if __name__ == "__main__":
    unittest.main()
