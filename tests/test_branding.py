"""Mutsu OS's public name must not break the existing technical IDs.

No GTK or live GNOME session is required for these regression checks.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from aidesktop.branding import AI_NAME, PRODUCT_NAME, SEARCH_NAME, WELCOME_TITLE

ROOT = Path(__file__).resolve().parents[1]


class BrandingTests(unittest.TestCase):
    def test_canonical_public_names(self):
        self.assertEqual(PRODUCT_NAME, "Mutsu OS")
        self.assertEqual(SEARCH_NAME, "Mutsu OS Search")
        self.assertEqual(AI_NAME, "Mutsu AI")
        self.assertEqual(WELCOME_TITLE, "Welcome to Mutsu OS")

    def test_brand_is_used_for_launcher_and_wizard(self):
        ui = (ROOT / "src/aidesktop/ui.py").read_text()
        wizard = (ROOT / "src/aidesktop/setup_wizard.py").read_text()
        cli = (ROOT / "src/aidesktop/__main__.py").read_text()
        ast.parse(ui)
        ast.parse(wizard)
        ast.parse(cli)
        self.assertIn("self.set_title(SEARCH_NAME)", ui)
        self.assertIn("self.set_title(WELCOME_TITLE)", wizard)
        self.assertIn('f"Ask {AI_NAME}"', ui)
        self.assertIn("from .branding import", ui)
        self.assertIn("from .branding import", wizard)
        self.assertIn('description=f"{PRODUCT_NAME} desktop prototype"', cli)

    def test_existing_user_identifiers_are_unchanged(self):
        ui = (ROOT / "src/aidesktop/ui.py").read_text()
        script = (ROOT / "scripts/install-local.sh").read_text()
        self.assertIn('application_id="io.github.markymark5127.AIDesktop"', ui)
        self.assertIn("io.github.markymark5127.AIDesktop.desktop", script)
        self.assertIn('~/.local/bin/ai-desktop', (ROOT / "docs/BRANDING.md").read_text())
        self.assertIn("Name=Mutsu OS Search", script)
        self.assertIn("GenericName=Application, File and AI Search", script)
        self.assertIn("Comment=Search Mutsu OS applications", script)

    def test_existing_shortcut_can_be_relabeled_without_rebinding(self):
        shortcut = (ROOT / "scripts/shortcut.py").read_text()
        installer = (ROOT / "scripts/install-desktop-experience.sh").read_text()
        self.assertIn('def refresh_label() -> None:', shortcut)
        self.assertIn('"Mutsu OS Search"', shortcut)
        self.assertIn("if command != expected:", shortcut)
        self.assertIn('"--refresh-label"', shortcut)
        self.assertIn("scripts/shortcut.py\" --refresh-label", installer)


if __name__ == "__main__":
    unittest.main()
