import subprocess
import unittest

from aidesktop import gsconnect


class Result:
    def __init__(self, code):
        self.returncode = code
        self.stdout = ""


class GSConnectTests(unittest.TestCase):
    def test_enable_turns_the_extension_on(self):
        calls = []

        def run(cmd, **_kw):
            calls.append(cmd)
            return Result(0)

        ok, message = gsconnect.enable_gsconnect(run)
        self.assertTrue(ok)
        self.assertIn(["gnome-extensions", "enable", gsconnect.GSCONNECT_ID], calls)
        self.assertIn("on", message)

    def test_missing_extension_is_reported_not_installed(self):
        ok, message = gsconnect.enable_gsconnect(lambda cmd, **_kw: Result(1))
        self.assertFalse(ok)
        self.assertIn("isn't installed", message)

    def test_timeout_is_handled(self):
        def run(cmd, **_kw):
            raise subprocess.TimeoutExpired(cmd, 5)
        ok, _ = gsconnect.enable_gsconnect(run)
        self.assertFalse(ok)

    def test_devices_parsed_paired_first(self):
        iface = gsconnect.DEVICE_IFACE
        managed = {
            "/d/a": {iface: {"Name": "Pixel", "Paired": False, "Connected": True, "Type": "phone"}},
            "/d/b": {iface: {"Name": "iPhone", "Paired": True, "Connected": True, "Type": "phone"}},
            "/d/c": {"org.freedesktop.DBus.Properties": {}},
        }
        devices = gsconnect.parse_devices(managed)
        self.assertEqual([d["name"] for d in devices], ["iPhone", "Pixel"])
        self.assertEqual(gsconnect.device_state(devices[0]), "Paired and connected")
        self.assertEqual(gsconnect.device_state(devices[1]), "Found · not paired yet")

    def test_pairing_steps_name_the_computer_and_fit_the_phone(self):
        ios = gsconnect.pairing_steps("iphone", "mutsu")
        self.assertTrue(any("local network" in s for s in ios))
        self.assertTrue(any("“mutsu”" in s for s in ios))
        android = gsconnect.pairing_steps("android", "mutsu")
        self.assertFalse(any("local network" in s for s in android))


if __name__ == "__main__":
    unittest.main()
