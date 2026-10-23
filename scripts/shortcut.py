#!/usr/bin/env python3
"""Opt-in GNOME Super+Space binding for the Mutsu OS Search launcher.

Usage: python3 scripts/shortcut.py --apply
       python3 scripts/shortcut.py --restore
No settings change is made without one of these flags.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
from pathlib import Path

MEDIA = "org.gnome.settings-daemon.plugins.media-keys"
WM = "org.gnome.desktop.wm.keybindings"
PATH = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/ai-desktop/"
CUSTOM = f"{MEDIA}.custom-keybinding:{PATH}"
BACKUP = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "ai-desktop/gnome-shortcut.json"


def read_string_array(value: str) -> list[str]:
    value = value.strip()
    if value == "@as []":
        return []
    parsed = ast.literal_eval(value)
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError(f"Expected a GSettings string array, got: {value}")
    return parsed


def _run(*argv: str) -> str:
    result = subprocess.run(["gsettings", *argv], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "gsettings command failed")
    return result.stdout.strip()


def _get_array(schema: str, key: str) -> list[str]:
    return read_string_array(_run("get", schema, key))


def _set_array(schema: str, key: str, values: list[str]) -> None:
    _run("set", schema, key, str(values) if values else "@as []")


def _set_string(schema: str, key: str, value: str) -> None:
    _run("set", schema, key, json.dumps(value))


def apply() -> None:
    launcher = Path.home() / ".local/bin/ai-desktop"
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise RuntimeError("Install the desktop launcher first: bash scripts/install-local.sh")
    if BACKUP.exists():
        raise RuntimeError(f"A backup already exists at {BACKUP}. Restore before applying again.")
    original = _get_array(MEDIA, "custom-keybindings")
    switch = _get_array(WM, "switch-input-source")
    if PATH in original:
        raise RuntimeError("A Mutsu OS shortcut path already exists; refusing to overwrite it.")
    for path in original:
        current = f"{MEDIA}.custom-keybinding:{path}"
        key = ast.literal_eval(_run("get", current, "binding"))
        if key.lower() == "<super>space":
            raise RuntimeError(f"Another custom shortcut already uses Super+Space: {path}")
    BACKUP.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(BACKUP, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump({"custom-keybindings": original, "switch-input-source": switch}, output)
    try:
        _set_string(CUSTOM, "name", "Mutsu OS Search")
        _set_string(CUSTOM, "command", str(launcher))
        _set_string(CUSTOM, "binding", "<Super>space")
        _set_array(MEDIA, "custom-keybindings", [*original, PATH])
        _set_array(WM, "switch-input-source", [item for item in switch if item.lower() != "<super>space"])
    except Exception:
        _set_array(MEDIA, "custom-keybindings", original)
        _set_array(WM, "switch-input-source", switch)
        raise
    print("Bound Super+Space to Mutsu OS Search. Original GNOME bindings saved to", BACKUP)
    print("Use --restore to put those bindings back.")


def restore() -> None:
    if not BACKUP.exists():
        raise RuntimeError("No shortcut backup exists, so no previous bindings can be restored.")
    settings = json.loads(BACKUP.read_text(encoding="utf-8"))
    _set_array(MEDIA, "custom-keybindings", settings["custom-keybindings"])
    _set_array(WM, "switch-input-source", settings["switch-input-source"])
    BACKUP.unlink()
    print("Restored the saved GNOME keyboard shortcuts.")



def refresh_label() -> None:
    """Rename only our existing saved Super+Space binding, not other shortcuts."""
    if not BACKUP.exists():
        print("No installed Mutsu OS shortcut backup; nothing to rename.")
        return
    existing = _get_array(MEDIA, "custom-keybindings")
    if PATH not in existing:
        raise RuntimeError("Saved Mutsu OS shortcut path is not registered in GNOME.")
    command = ast.literal_eval(_run("get", CUSTOM, "command"))
    expected = str(Path.home() / ".local/bin/ai-desktop")
    if command != expected:
        raise RuntimeError("Shortcut points to another command; refusing to relabel it.")
    old_label = ast.literal_eval(_run("get", CUSTOM, "name"))
    if old_label not in ("AI Desktop", "Mutsu Search", "Mutsu OS Search"):
        print(f"Keeping your custom shortcut label: {old_label}")
        return
    _set_string(CUSTOM, "name", "Mutsu OS Search")
    print("Renamed existing Super+Space shortcut to Mutsu OS Search.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--apply", action="store_true", help="Enable the Mutsu OS Search shortcut")
    group.add_argument("--restore", action="store_true", help="Restore original bindings")
    group.add_argument(
        "--refresh-label", action="store_true",
        help="Update the existing AI Desktop/Mutsu shortcut display name only",
    )
    args = parser.parse_args()
    try:
        if args.apply:
            apply()
        elif args.restore:
            restore()
        else:
            refresh_label()
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"Shortcut configuration failed: {exc}\n")


if __name__ == "__main__":
    main()
