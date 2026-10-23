"""Reversible user-scoped GNOME Dock setup.

Dash to Dock must already be installed AND enabled. This module never installs
shell extensions, reloads GNOME Shell, or modifies the Activities/overview UI.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

DOCK_SCHEMA = "org.gnome.shell.extensions.dash-to-dock"
EXTENSION_IDS = ("dash-to-dock@micxgx.gmail.com", "ubuntu-dock@ubuntu.com")
POSITIONS = ("BOTTOM", "LEFT", "RIGHT", "TOP")
MANAGED_KEYS = (
    "dock-position", "dock-fixed", "autohide", "intellihide",
    "manualhide", "show-show-apps-button", "show-apps-at-top", "extend-height",
)


class DockError(Exception):
    pass


def _command(*args: str) -> str:
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, check=False, timeout=6
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DockError("Cannot read GNOME dock settings in this session.") from exc
    if result.returncode:
        raise DockError("GNOME rejected a dock settings operation.")
    return result.stdout.strip()


def _schema_available() -> bool:
    return DOCK_SCHEMA in _command("gsettings", "list-schemas").splitlines()


def _enabled_extension() -> str | None:
    try:
        installed = set(_command("gnome-extensions", "list", "--enabled").splitlines())
    except DockError:
        return None
    return next((name for name in EXTENSION_IDS if name in installed), None)


def dock_status() -> str:
    if not _schema_available():
        return (
            "Dash to Dock settings were not found. Check the installed GNOME "
            "extensions in Extension Manager before applying the Mac dock layout."
        )
    if not _enabled_extension():
        return (
            "Dash to Dock is not enabled. Open Extension Manager to install or "
            "enable a version compatible with your GNOME Shell release."
        )
    position = _command("gsettings", "get", DOCK_SCHEMA, "dock-position")
    fixed = _command("gsettings", "get", DOCK_SCHEMA, "dock-fixed")
    return f"Dash to Dock enabled. Position: {position}; always visible: {fixed}."


def _get(name: str) -> str:
    return _command("gsettings", "get", DOCK_SCHEMA, name)


def _set(name: str, value: str) -> None:
    if name not in MANAGED_KEYS:
        raise DockError("Unsupported dock preference.")
    _command("gsettings", "set", DOCK_SCHEMA, name, value)


def backup_path() -> Path:
    root = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    return root / "ai-desktop" / "dock-backup.json"


def settings_for(position: str, always_visible: bool) -> dict[str, str]:
    if position not in POSITIONS:
        raise DockError("Dock position must be Bottom, Left, Right or Top.")
    # A fixed dock does not require entering the GNOME Overview to appear.
    return {
        "dock-position": f"'{position}'",
        "dock-fixed": "true" if always_visible else "false",
        "autohide": "false" if always_visible else "true",
        "intellihide": "false",
        "manualhide": "false",
        "show-show-apps-button": "true",
        "show-apps-at-top": "true",
        "extend-height": "false",
    }


def apply_dock(position: str = "BOTTOM", always_visible: bool = True) -> str:
    desired = settings_for(position, always_visible)
    if not _schema_available() or not _enabled_extension():
        raise DockError(
            "Dash to Dock must be installed and enabled first. Use GNOME "
            "Extension Manager, then try Apply again."
        )
    previous = {key: _get(key) for key in MANAGED_KEYS}
    path = backup_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Exclusive creation ensures future changes never overwrite the original.
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"schema": DOCK_SCHEMA, "values": previous}, stream)
            stream.write("\n")
    applied = []
    try:
        for key, value in desired.items():
            if value != previous[key]:
                _set(key, value)
                applied.append(key)
    except DockError:
        for key in reversed(applied):
            try:
                _set(key, previous[key])
            except DockError:
                pass
        raise
    return (
        f"Configured {position.title()} dock; {'always visible' if always_visible else 'auto-hide'}; "
        "Applications grid button enabled. Use Restore original dock to undo."
    )


def restore_dock() -> str:
    path = backup_path()
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DockError("There is no saved dock configuration to restore.") from exc
    except (OSError, ValueError) as exc:
        raise DockError("The saved dock configuration cannot be read.") from exc
    if (
        not isinstance(saved, dict)
        or saved.get("schema") != DOCK_SCHEMA
        or not isinstance(saved.get("values"), dict)
        or set(saved["values"]) != set(MANAGED_KEYS)
        or not all(isinstance(value, str) and len(value) < 64 for value in saved["values"].values())
    ):
        raise DockError("The dock backup format is invalid.")
    if not _schema_available():
        raise DockError("The original dock extension settings are unavailable.")
    for key in MANAGED_KEYS:
        _set(key, saved["values"][key])
    path.unlink()
    return "Original GNOME dock settings restored."
