"""Small, app-scoped presentation themes for AI Desktop.

This module deliberately has no GTK dependency so it can be tested headlessly.
Themes affect only the AI Desktop window, not every GNOME application.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


THEME_LABELS = [
    ("System", "system"),
    ("Japandi", "japandi"),
    ("Cyberpunk", "cyberpunk"),
]

# GTK4 CSS, scoped entirely to the root class added by ui.py.
# Fonts fall back to the user's configured GNOME typeface.
COMMON = """
.ai-desktop {
  padding: 0;
}
.ai-desktop entry {
  min-height: 46px;
  border-radius: 12px;
  padding-left: 12px;
  padding-right: 12px;
}
.ai-desktop scrolledwindow {
  border-radius: 12px;
}
.ai-desktop listbox {
  border-radius: 12px;
}
.ai-desktop listbox row {
  border-radius: 8px;
}
.ai-desktop button {
  min-height: 32px;
  border-radius: 9px;
}
"""

# We intentionally scope colored title buttons to AI Desktop windows. Applying
# left-side controls OS-wide is a separate, reversible GNOME user preference;
# Qt/Electron apps can provide their own decorations.
WINDOW_BUTTONS = """
/* These are our own non-stretching 13px GTK Buttons, not GNOME's tall
   windowcontrols buttons; keep normal headerbar controls fully separate. */
window.ai-desktop-window headerbar .mac-stoplights {
  background: transparent;
  border: none;
  box-shadow: none;
}
window.ai-desktop-window headerbar button.mac-stoplight {
  min-width: 13px;
  min-height: 13px;
  padding: 0;
  margin: 0;
  border-radius: 999px;
  background-image: none;
  box-shadow: inset 0 1px rgba(255,255,255,0.22);
}
window.ai-desktop-window headerbar button.mac-stoplight.mac-close {
  background-color: #ff5f57;
  border: 1px solid #df514e;
}
window.ai-desktop-window headerbar button.mac-stoplight.mac-minimize {
  background-color: #febc2e;
  border: 1px solid #dba224;
}
window.ai-desktop-window headerbar button.mac-stoplight.mac-maximize {
  background-color: #28c840;
  border: 1px solid #1fae37;
}
window.ai-desktop-window headerbar button.mac-stoplight:hover {
  box-shadow: 0 0 0 2px rgba(180,180,180,0.40);
}
window.ai-desktop-window headerbar button.mac-stoplight:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 3px;
}
"""

JAPANDI = """
.ai-desktop.japandi,
window.ai-desktop-window.japandi {
  background-color: #f3efe7;
  color: #303832;
}
window.ai-desktop-window.japandi headerbar {
  background-color: #f3efe7;
  color: #303832;
  box-shadow: none;
}
.ai-desktop.japandi entry {
  background-color: #fffdf9;
  color: #303832;
  border: 1px solid #c6c7b7;
  box-shadow: none;
}
.ai-desktop.japandi listbox {
  background-color: #fffcf6;
  color: #303832;
  border: 1px solid #d9d7cc;
}
.ai-desktop.japandi listbox row:selected {
  background-color: #dce5d9;
  color: #263b2d;
}
.ai-desktop.japandi textview,
.ai-desktop.japandi textview text {
  background-color: #fffcf6;
  color: #303832;
}
.ai-desktop.japandi button.suggested-action {
  background-color: #516b5c;
  color: #ffffff;
  border: 1px solid #516b5c;
}
.ai-desktop.japandi button.suggested-action:hover {
  background-color: #405849;
}
"""

CYBERPUNK = """
/* Deliberately distinct from Adwaita Dark: angular retro-terminal panels,
   cyan/magenta borders, thin neon glow and monospace/pixel-font fallback. */
window.ai-desktop-window.cyberpunk,
.ai-desktop.cyberpunk,
window.ai-desktop-window.cyberpunk toolbarview {
  background-color: #080c16;
  color: #ebfdff;
}
window.ai-desktop-window.cyberpunk headerbar {
  background-color: #111125;
  color: #00f5ff;
  font-family: "Press Start 2P", "Pixeloid Sans", monospace;
  font-weight: 700;
  border-bottom: 2px solid #00f5ff;
  box-shadow: 0 3px 12px rgba(0,245,255,0.35);
  border-radius: 0;
}
window.ai-desktop-window.cyberpunk headerbar button:not(.mac-stoplight),
window.ai-desktop-window.cyberpunk headerbar dropdown > button {
  color: #ecfcff;
  background-color: #1c1737;
  background-image: none;
  border: 1px solid #ff36ba;
  border-radius: 0;
  box-shadow: 0 0 6px rgba(255,54,186,0.36);
}
.ai-desktop.cyberpunk {
  font-family: "Pixeloid Sans", "DejaVu Sans Mono", monospace;
}
.ai-desktop.cyberpunk .title-1 {
  font-family: "Press Start 2P", "Pixeloid Sans", monospace;
  font-weight: 800;
  color: #00f5ff;
  text-shadow: 0 0 10px rgba(0,245,255,0.6);
}
.ai-desktop.cyberpunk .dim-label {
  color: #9ab5d0;
}
.ai-desktop.cyberpunk entry,
.ai-desktop.cyberpunk textview,
.ai-desktop.cyberpunk textview text {
  color: #e9fdff;
  background-color: #0a1428;
  background-image: none;
  border: 1px solid #00f5ff;
  border-radius: 0;
  box-shadow: inset 0 0 0 1px rgba(0,245,255,0.16),
              0 0 10px rgba(0,245,255,0.30);
  font-family: monospace;
}
.ai-desktop.cyberpunk entry:focus-within {
  border-color: #ff36ba;
  box-shadow: 0 0 12px rgba(255,54,186,0.55);
}
.ai-desktop.cyberpunk scrolledwindow,
.ai-desktop.cyberpunk listbox,
.ai-desktop.cyberpunk box,
.ai-desktop.cyberpunk stack {
  border-radius: 0;
}
.ai-desktop.cyberpunk listbox {
  color: #e9fdff;
  background-color: #0c1427;
  border: 1px solid #00f5ff;
  box-shadow: 0 0 10px rgba(0,245,255,0.18);
}
.ai-desktop.cyberpunk listbox row {
  border-radius: 0;
  border-bottom: 1px solid rgba(0,245,255,0.20);
}
.ai-desktop.cyberpunk listbox row:selected {
  background-color: #2e1440;
  color: #ffffff;
  border-left: 3px solid #ff36ba;
}
.ai-desktop.cyberpunk button,
.ai-desktop.cyberpunk dropdown > button {
  color: #e9fdff;
  background-color: #15182e;
  background-image: none;
  border: 1px solid #00f5ff;
  border-radius: 0;
  box-shadow: 0 0 8px rgba(0,245,255,0.20);
  font-family: monospace;
  font-weight: 700;
}
.ai-desktop.cyberpunk button:hover,
.ai-desktop.cyberpunk dropdown > button:hover {
  background-color: #261b47;
  border-color: #ff36ba;
  box-shadow: 0 0 12px rgba(255,54,186,0.45);
}
.ai-desktop.cyberpunk button.suggested-action {
  color: #080c16;
  background-color: #00f5ff;
  border: 2px solid #00f5ff;
  border-radius: 0;
  box-shadow: 0 0 16px rgba(0,245,255,0.60);
}
.ai-desktop.cyberpunk button.suggested-action:hover {
  color: #ffffff;
  background-color: #7c135e;
  border-color: #ff36ba;
  box-shadow: 0 0 17px rgba(255,54,186,0.72);
}
.ai-desktop.cyberpunk checkbutton check {
  background-color: #0a1428;
  border: 1px solid #ff36ba;
  border-radius: 0;
}
.ai-desktop.cyberpunk checkbutton check:checked {
  background-color: #ff36ba;
}
.ai-desktop.cyberpunk progressbar trough {
  background-color: #15182e;
  border: 1px solid #00f5ff;
  border-radius: 0;
}
.ai-desktop.cyberpunk progressbar progress {
  background-color: #ff36ba;
  border-radius: 0;
}
"""

STYLES = {
    "system": WINDOW_BUTTONS,
    "japandi": COMMON + WINDOW_BUTTONS + JAPANDI,
    "cyberpunk": COMMON + WINDOW_BUTTONS + CYBERPUNK,
}

# Spotlight is a separate, deliberately small surface. These rules apply ONLY
# to the launcher window, after the normal app-scoped theme. Translucency is
# CSS alpha; GNOME/Wayland does not provide a portable app-controlled blur.
SPOTLIGHT_COMMON = """
window.ai-desktop-window.spotlight-window {
  background-color: transparent;
  background-image: none;
  border: none;
  box-shadow: none;
}
window.spotlight-window .ai-desktop.spotlight-shell {
  margin: 8px;
  padding: 5px 10px;
  border-radius: 18px;
}
window.spotlight-window .ai-desktop.spotlight-shell entry.spotlight-entry {
  min-height: 52px;
  padding: 2px 8px;
  border: none;
  background: transparent;
  background-image: none;
  box-shadow: none;
  font-size: 17px;
}
window.spotlight-window .ai-desktop.spotlight-shell entry.spotlight-entry:focus {
  outline: none;
  box-shadow: none;
}
window.spotlight-window .spotlight-searchbar menubutton.spotlight-settings-button > button {
  min-width: 30px;
  min-height: 30px;
  margin: 0 3px;
  padding: 1px;
  border: none;
  border-radius: 8px;
  background: transparent;
  box-shadow: none;
}
window.spotlight-window .spotlight-searchbar menubutton.spotlight-settings-button > button:hover {
  background-color: rgba(127, 127, 127, 0.16);
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-results,
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-response {
  padding-bottom: 4px;
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-approval {
  padding: 2px 12px 9px;
}
window.spotlight-window .ai-desktop.spotlight-shell listbox.spotlight-list,
window.spotlight-window .ai-desktop.spotlight-shell listbox.spotlight-list row {
  border: 0;
  box-shadow: none;
}
window.spotlight-window .ai-desktop.spotlight-shell textview.spotlight-output,
window.spotlight-window .ai-desktop.spotlight-shell textview.spotlight-output text {
  background: transparent;
  border: none;
  box-shadow: none;
}
window.spotlight-window .ai-desktop.spotlight-shell separator {
  min-height: 1px;
}
"""

SPOTLIGHT_STYLES = {
    "system": SPOTLIGHT_COMMON + """
window.spotlight-window .ai-desktop.spotlight-shell {
  background-color: rgba(38, 42, 51, 0.90);
  color: #f8f9fc;
  border: 1px solid rgba(233, 237, 246, 0.20);
  box-shadow: 0 9px 28px rgba(0, 0, 0, 0.28);
}
window.spotlight-window .ai-desktop.spotlight-shell entry.spotlight-entry,
window.spotlight-window .ai-desktop.spotlight-shell textview.spotlight-output {
  color: #ffffff;
}
window.spotlight-window .ai-desktop.spotlight-shell listbox.spotlight-list {
  background-color: transparent;
  color: #f8f9fc;
}
window.spotlight-window .ai-desktop.spotlight-shell listbox row:selected {
  background-color: rgba(255,255,255,0.18);
}
""",
    "japandi": SPOTLIGHT_COMMON + """
window.spotlight-window .ai-desktop.spotlight-shell.japandi {
  background-color: rgba(243, 239, 231, 0.88);
  color: #303832;
  border: 1px solid rgba(104, 117, 97, 0.40);
  border-radius: 20px;
  box-shadow: 0 9px 26px rgba(40, 51, 45, 0.20);
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi entry.spotlight-entry,
window.spotlight-window .ai-desktop.spotlight-shell.japandi textview.spotlight-output,
window.spotlight-window .ai-desktop.spotlight-shell.japandi textview.spotlight-output text {
  background: transparent;
  border: none;
  color: #303832;
  box-shadow: none;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi listbox.spotlight-list {
  background: transparent;
  border: none;
  color: #303832;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi listbox row:selected {
  background-color: rgba(81, 107, 92, 0.17);
  border-radius: 10px;
}
""",
    "cyberpunk": SPOTLIGHT_COMMON + """
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk {
  background-color: rgba(8, 12, 22, 0.90);
  color: #ebfdff;
  border: 1px solid #00f5ff;
  border-radius: 0;
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.32);
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk entry.spotlight-entry,
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk textview.spotlight-output,
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk textview.spotlight-output text {
  background: transparent;
  border: 0;
  border-radius: 0;
  color: #ebfdff;
  box-shadow: none;
  font-family: monospace;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk listbox.spotlight-list {
  background: transparent;
  border: none;
  color: #ebfdff;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk listbox row:selected {
  background-color: rgba(255, 54, 186, 0.25);
  border-left: 3px solid #ff36ba;
  border-radius: 0;
}
""",
}

SPOTLIGHT_HIGH_CONTRAST = """
window.ai-desktop-window.spotlight-window {
  background-color: transparent;
}
window.spotlight-window .ai-desktop.spotlight-shell {
  padding: 8px;
  background-color: #101010;
  color: #ffffff;
  border: 2px solid #ffffff;
  border-radius: 8px;
}
window.spotlight-window .ai-desktop.spotlight-shell entry.spotlight-entry,
window.spotlight-window .ai-desktop.spotlight-shell textview.spotlight-output,
window.spotlight-window .ai-desktop.spotlight-shell textview.spotlight-output text {
  background: #101010;
  color: #ffffff;
}
"""

SCHEMES = {"system": "default", "japandi": "light", "cyberpunk": "dark"}


def config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "ai-desktop" / "appearance.json"


def validate_theme(name: str) -> str:
    if name not in STYLES:
        raise ValueError("Unknown theme")
    return name


def load_theme() -> str:
    try:
        with config_path().open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, ValueError):
        return "japandi"
    if not isinstance(value, dict) or value.get("theme") not in STYLES:
        return "japandi"
    return value["theme"]


def save_theme(name: str) -> None:
    name = validate_theme(name)
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".appearance-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"theme": name}, stream)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
