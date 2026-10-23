"""Headless checks for Spotlight lifecycle, AI row and CSS provider cleanup.

These inspect source structure only. Live GTK/Wayland behavior still needs
visual testing on Bazzite, where compositor focus transitions vary.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "src/aidesktop/ui.py"
WIZARD = ROOT / "src/aidesktop/setup_wizard.py"


def method_source(path: Path, klass: str, method: str) -> str:
    content = path.read_text(encoding="utf-8")
    tree = ast.parse(content)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == klass)
    func = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method)
    return ast.get_source_segment(content, func) or ""


class SpotlightLifecycleTests(unittest.TestCase):
    def test_unfocused_idle_launcher_closes_instead_of_lingering(self):
        source = method_source(UI, "AssistantWindow", "_dismiss_if_unfocused")
        self.assertIn("should_hide_on_focus_loss(", source)
        self.assertIn("if self.busy or self.pending is not None:", source)
        self.assertIn("self.hide()", source)
        self.assertIn("self.close()", source)

    def test_ai_only_row_is_full_size_and_no_divider(self):
        constructor = method_source(UI, "AssistantWindow", "__init__")
        update = method_source(UI, "AssistantWindow", "_update_results")
        self.assertIn("self.results_divider = Gtk.Separator()", constructor)
        self.assertIn('search_scroll.add_css_class("spotlight-scroll")', constructor)
        self.assertIn("content.set_size_request(-1, 62)", update)
        self.assertIn("row.add_css_class(\"spotlight-ask-row\")", update)
        self.assertIn("self.results_divider.set_visible(not ai_only)", update)
        self.assertIn('self.results_section.add_css_class("spotlight-ai-only")', update)
        self.assertIn("self.results.select_row(self.results.get_row_at_index(0))", update)

    def test_recreated_windows_remove_old_display_css(self):
        for path, klass, provider in (
            (UI, "AssistantWindow", "self._theme_provider"),
            (WIZARD, "SetupWizard", "self.css"),
        ):
            with self.subTest(window=klass):
                constructor = method_source(path, klass, "__init__")
                cleanup = method_source(path, klass, "_remove_theme_provider")
                self.assertIn('self.connect("close-request", self._remove_theme_provider)', constructor)
                self.assertIn("Gtk.StyleContext.remove_provider_for_display(", cleanup)
                self.assertIn(provider, cleanup)
                self.assertIn("return False", cleanup)

    def test_wallpaper_directory_contains_exact_contract(self):
        asset_readme = (
            ROOT / "assets/wallpapers/README.md"
        ).read_text(encoding="utf-8")
        self.assertIn("mutsu-japandi-4k.png", asset_readme)
        self.assertIn("mutsu-cyberpunk-4k.png", asset_readme)
        self.assertIn("3840 × 2160", asset_readme)
        self.assertIn("/usr/share/backgrounds/mutsu/", asset_readme)


if __name__ == "__main__":
    unittest.main()
