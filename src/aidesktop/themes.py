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

JAPANDI = """
.ai-desktop {
  background-color: #f3efe7;
  color: #303832;
}
.ai-desktop headerbar {
  background-color: #f3efe7;
  color: #303832;
  box-shadow: none;
}
.ai-desktop entry {
  background-color: #fffdf9;
  color: #303832;
  border: 1px solid #c6c7b7;
  box-shadow: none;
}
.ai-desktop listbox {
  background-color: #fffcf6;
  color: #303832;
  border: 1px solid #d9d7cc;
}
.ai-desktop listbox row:selected {
  background-color: #dce5d9;
  color: #263b2d;
}
.ai-desktop textview,
.ai-desktop textview text {
  background-color: #fffcf6;
  color: #303832;
}
.ai-desktop button.suggested-action {
  background-color: #516b5c;
  color: #ffffff;
  border: 1px solid #516b5c;
}
.ai-desktop button.suggested-action:hover {
  background-color: #405849;
}
"""

CYBERPUNK = """
.ai-desktop {
  background-color: #121522;
  color: #eef4ff;
}
.ai-desktop headerbar {
  background-color: #121522;
  color: #eef4ff;
  box-shadow: none;
}
.ai-desktop entry {
  background-color: #1e2333;
  color: #f2f7ff;
  border: 1px solid #50dce3;
  box-shadow: none;
}
.ai-desktop listbox {
  background-color: #1c2130;
  color: #f2f7ff;
  border: 1px solid #3a405c;
}
.ai-desktop listbox row:selected {
  background-color: #303551;
  color: #f5faff;
}
.ai-desktop textview,
.ai-desktop textview text {
  background-color: #1c2130;
  color: #eef4ff;
}
.ai-desktop button.suggested-action {
  background-color: #b62d7e;
  color: #ffffff;
  border: 1px solid #ed69bd;
}
.ai-desktop button.suggested-action:hover {
  background-color: #d53696;
}
"""

STYLES = {
    "system": "",
    "japandi": COMMON + JAPANDI,
    "cyberpunk": COMMON + CYBERPUNK,
}
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
