"""Mac-like left-side GNOME titlebar buttons with safe, reversible settings.

Per-user GNOME window-manager layout is global to cooperating applications.
Colors for AI Desktop itself come from its scoped GTK CSS; Qt/Electron apps
and sandboxed applications may render their own independent titlebars.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
from pathlib import Path


SCHEMA = "org.gnome.desktop.wm.preferences"
KEY = "button-layout"
MAC_LAYOUT = "close,minimize,maximize:"
VALID_LAYOUT = re.compile(r"[a-z,:-]{1,128}")


class WindowLayoutError(Exception):
    pass


def backup_path() -> Path:
    root = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    return root / "ai-desktop" / "window-buttons-backup.json"


def _gsettings(*args: str) -> str:
    try:
        result = subprocess.run(
            ["gsettings", *args], check=False, text=True,
            capture_output=True, timeout=6,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WindowLayoutError("GNOME window settings are unavailable.") from exc
    if result.returncode:
        raise WindowLayoutError("GNOME could not change the window-button arrangement.")
    return result.stdout.strip()


def current_layout() -> str:
    raw = _gsettings("get", SCHEMA, KEY)
    try:
        layout = ast.literal_eval(raw)
    except (SyntaxError, ValueError) as exc:
        raise WindowLayoutError("Could not read the GNOME window layout.") from exc
    if not isinstance(layout, str) or not VALID_LAYOUT.fullmatch(layout):
        raise WindowLayoutError("GNOME returned an unexpected window layout.")
    return layout


def describe_layout() -> str:
    current = current_layout()
    if current == MAC_LAYOUT:
        return "GNOME already has left-side Close, Minimize and Maximize buttons."
    return f"GNOME currently uses: {current}. You can apply left-side Mac-style controls."


def apply_mac_layout() -> str:
    existing = current_layout()
    if existing == MAC_LAYOUT:
        return "GNOME window buttons are already on the left."
    path = backup_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"schema": SCHEMA, "key": KEY, "value": existing}, stream)
            stream.write("\n")
    _gsettings("set", SCHEMA, KEY, MAC_LAYOUT)
    if current_layout() != MAC_LAYOUT:
        raise WindowLayoutError("The window-layout change could not be verified.")
    return (
        "GNOME's Close, Minimize and Maximize buttons are now on the left. "
        "AI Desktop renders these as red/yellow/green stoplights. Other apps "
        "may use their own titlebars and colors. You can restore your prior layout."
    )


def restore_previous_layout() -> str:
    path = backup_path()
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WindowLayoutError("No original window layout was saved.") from exc
    except (OSError, ValueError) as exc:
        raise WindowLayoutError("Cannot read the original window layout backup.") from exc
    if (
        not isinstance(stored, dict)
        or set(stored) != {"schema", "key", "value"}
        or stored["schema"] != SCHEMA
        or stored["key"] != KEY
        or not isinstance(stored["value"], str)
        or not VALID_LAYOUT.fullmatch(stored["value"])
    ):
        raise WindowLayoutError("The original window-layout backup is invalid.")
    _gsettings("set", SCHEMA, KEY, stored["value"])
    if current_layout() != stored["value"]:
        raise WindowLayoutError("GNOME could not verify the restored layout.")
    path.unlink()
    return "GNOME's previous window-button layout was restored."
