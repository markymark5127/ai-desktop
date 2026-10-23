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

    def test_search_groups_and_ai_result_remain_keyboard_selectable(self):
        constructor = method_source(UI, "AssistantWindow", "__init__")
        update = method_source(UI, "AssistantWindow", "_update_results")
        heading = method_source(UI, "AssistantWindow", "_append_heading")
        key = method_source(UI, "AssistantWindow", "_on_key")
        self.assertIn("self.results_divider = Gtk.Separator()", constructor)
        self.assertIn('search_scroll.add_css_class("spotlight-scroll")', constructor)
        self.assertIn("self.files_catalog: list[FileResult]", constructor)
        self.assertIn('self._append_heading("Top Results")', update)
        self.assertIn('self._append_heading("Files")', update)
        self.assertIn('self._append_heading("AI Suggestions")', update)
        self.assertIn('"Ask Mutsu AI"', update)
        self.assertIn("self.results_divider.set_visible(False)", update)
        self.assertIn("self.selectable_indices[0]", update)
        self.assertIn("self.selectable_indices", key)
        self.assertIn("row.set_selectable(False)", heading)
        self.assertIn("row.set_activatable(False)", heading)

    def test_local_file_search_is_off_main_typing_path(self):
        constructor = method_source(UI, "AssistantWindow", "__init__")
        start = method_source(UI, "AssistantWindow", "_begin_file_scan")
        update = method_source(UI, "AssistantWindow", "_update_results")
        open_file = method_source(UI, "AssistantWindow", "_open_file")
        self.assertIn("GLib.idle_add(self._begin_file_scan)", constructor)
        self.assertIn("threading.Thread(target=worker", start)
        self.assertIn("search_local_files(", update)
        self.assertNotIn("list_local_files()", update)
        self.assertIn("Gio.AppInfo.launch_default_for_uri", open_file)

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
