"""Brand artwork inventory and safe Mutsu image-layer regression checks."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-brand-assets.py"
spec = importlib.util.spec_from_file_location("mutsu_brand_checker", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class BrandAssetTests(unittest.TestCase):
    def test_svg_validator_accepts_owner_vector_and_rejects_html(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            svg = base / "mutsu-logo-symbol.svg"
            svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0,0 L1,1"/></svg>')
            self.assertEqual(checker.valid_svg(svg), (True, "ready"))
            bad = base / "fake.svg"
            bad.write_text("<html></html>")
            self.assertFalse(checker.valid_svg(bad)[0])
            self.assertFalse(checker.valid_svg(base / "missing.svg")[0])

    def test_inventory_only_requires_three_core_icons(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            icons = home / "icons"
            wallpapers = home / "wallpapers"
            icons.mkdir()
            wallpapers.mkdir()
            with patch.object(checker, "ROOT", home):
                with patch.object(checker, "ICON_DIR", icons):
                    with patch.object(checker, "WALLPAPER_DIR", wallpapers):
                        report, missing = checker.audit()
                        self.assertEqual(missing, 3)
                        self.assertIn("mutsu-logo-symbolic.svg", "\n".join(report))
                        self.assertIn("mutsu-logo-wordmark.svg", "\n".join(report))
                        for name in checker.REQUIRED:
                            (icons / name).write_text(
                                '<svg xmlns="http://www.w3.org/2000/svg"/>'
                            )
                        report, missing = checker.audit()
                        self.assertEqual(missing, 0)

    def test_user_installer_does_not_edit_system_logo(self):
        script = (ROOT / "scripts/install-local.sh").read_text()
        self.assertIn('icon_source="$repo_dir/assets/icons/mutsu-logo-symbol.svg"', script)
        self.assertIn('icon_dir="$HOME/.local/share/icons/hicolor/scalable/apps"', script)
        self.assertIn("Icon=$icon_value", script)
        self.assertNotIn("sudo ", script)
        self.assertNotIn("rm -rf /usr", script)

    def test_image_overlay_keeps_upstream_identifiers(self):
        builder = (ROOT / "packaging/mutsu-image/install-branding.sh").read_text()
        image = (ROOT / "packaging/mutsu-image/Containerfile").read_text()
        self.assertIn("FROM ${BASE_IMAGE}", image)
        self.assertIn("PRETTY_NAME", builder)
        self.assertIn('"Mutsu OS"', builder)
        self.assertIn('"LOGO": "mutsu-os-logo"', builder)
        self.assertIn("[org/gnome/login-screen]", builder)
        self.assertIn("dconf update", builder)
        self.assertNotIn('"ID":', builder)
        self.assertNotIn('"ID_LIKE":', builder)
        self.assertNotIn('"VERSION_ID":', builder)
        self.assertNotIn("plymouth-set-default-theme", builder)
        self.assertNotIn("dracut -f", builder)


if __name__ == "__main__":
    unittest.main()
