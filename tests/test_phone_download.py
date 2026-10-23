import unittest

from aidesktop.phone_download import app_info, qr_matrix


class PhoneDownloadTests(unittest.TestCase):
    def test_qr_targets_official_app_stores(self):
        self.assertEqual(
            app_info("iphone")["url"],
            "https://apps.apple.com/us/app/kde-connect/id1580245991",
        )
        self.assertEqual(
            app_info("android")["url"],
            "https://play.google.com/store/apps/details?id=org.kde.kdeconnect_tp",
        )

    def test_matrices_have_quiet_zones_and_finder_patterns(self):
        for phone in ("iphone", "android"):
            with self.subTest(phone=phone):
                data = qr_matrix(phone)
                size = len(data)
                self.assertEqual(size, app_info(phone)["size"])
                self.assertTrue(all(len(row) == size for row in data))
                # Four white modules are essential to scanning.
                for i in range(4):
                    self.assertFalse(any(data[i]))
                    self.assertFalse(any(data[-1-i]))
                    self.assertFalse(any(row[i] or row[-1-i] for row in data))
                # Top-left and top-right position-detection patterns begin at (4,4).
                for y, x in ((4, 4), (4, size-11), (size-11, 4)):
                    self.assertTrue(data[y][x])
                    self.assertTrue(data[y + 6][x + 6])
                    self.assertFalse(data[y+1][x+1])

    def test_later_has_no_code(self):
        with self.assertRaises(ValueError):
            qr_matrix("later")


if __name__ == "__main__":
    unittest.main()
