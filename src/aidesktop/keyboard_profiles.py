"""Optional Mac/PC US keyboard presets for GNOME.

Choosing a profile affects AI Desktop shortcut labels immediately. Applying an
XKB input layout to GNOME is a separate *explicit* user action.

On typical Apple keyboards Linux already maps physical Command to Super; the
Macintosh US XKB symbols variant does not independently guarantee a modifier
remap on every keyboard/VM.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import tempfile
from pathlib import Path


PROFILES = (
    ("Windows keyboard, Mac shortcuts", "windows-mac"),
    ("Windows keyboard, standard shortcuts", "standard"),
    ("Mac keyboard", "mac"),
)
LAYOUT_IDS = {"windows-mac": "us", "standard": "us", "mac": "us+mac"}
SCHEMA = "org.gnome.desktop.input-sources"


class KeyboardError(Exception):
    pass


def validate(profile: str) -> str:
    if profile not in LAYOUT_IDS:
        raise ValueError("Unknown keyboard profile")
    return profile


def config_root() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "ai-desktop"


def state_root() -> Path:
    return Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state") / "ai-desktop"


def preference_path() -> Path:
    return config_root() / "keyboard.json"


def backup_path() -> Path:
    return state_root() / "keyboard-sources-backup.json"


def _atomic_private_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".keyboard-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def get_profile() -> str:
    try:
        data = json.loads(preference_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "standard"
    if not isinstance(data, dict) or data.get("profile") not in LAYOUT_IDS:
        return "standard"
    return data["profile"]


def set_profile(profile: str) -> None:
    _atomic_private_json(preference_path(), {"profile": validate(profile)})


def mac_shortcuts_wanted(profile: str) -> bool:
    return validate(profile) == "windows-mac"


def keyd_active() -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "keyd"],
            text=True, capture_output=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.stdout.strip() == "active"


def set_keyd(enabled: bool) -> str:
    """Start or stop the Mac-shortcut mapper. Needs a privileged systemctl."""
    action = "start" if enabled else "stop"
    commands = (
        ["systemctl", action, "keyd"],
        ["pkexec", "systemctl", action, "keyd"],
    )
    last = "keyd could not be changed"
    for argv in commands:
        try:
            result = subprocess.run(argv, text=True, capture_output=True, timeout=20, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            last = str(exc)
            continue
        if result.returncode == 0:
            state = "on" if enabled else "off"
            return f"Mac shortcuts are {state}."
        last = (result.stderr or result.stdout or "systemctl failed").strip()
    raise KeyboardError(last)


def super_label(profile: str) -> str:
    return "⌘ Command" if validate(profile) == "mac" else "Win / Super"


def shortcut_label(profile: str) -> str:
    return "⌘ + Space" if validate(profile) == "mac" else "Win + Space"


def parse_sources(text: str) -> list[tuple[str, str]]:
    """Parse GSettings a(ss) output with no eval() or untrusted code."""
    text = text.strip()
    if text.startswith("@a(ss) "):
        text = text.removeprefix("@a(ss) ").strip()
    try:
        values = ast.literal_eval(text)
    except (SyntaxError, ValueError) as exc:
        raise KeyboardError("Could not understand existing GNOME keyboard layouts") from exc
    if not isinstance(values, list):
        raise KeyboardError("Unexpected GNOME keyboard layout format")
    sources: list[tuple[str, str]] = []
    for item in values:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not all(isinstance(value, str) and 0 < len(value) < 128 for value in item)
        ):
            raise KeyboardError("Unexpected GNOME keyboard source entry")
        sources.append(item)
    return sources


def prepend_layout(profile: str, sources: list[tuple[str, str]]) -> list[tuple[str, str]]:
    target = ("xkb", LAYOUT_IDS[validate(profile)])
    return [target, *(item for item in sources if item != target)]


def _gsettings(*args: str) -> str:
    try:
        result = subprocess.run(
            ["gsettings", *args], text=True, capture_output=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise KeyboardError("GNOME keyboard settings could not be reached") from exc
    if result.returncode:
        raise KeyboardError("GNOME rejected the keyboard layout change")
    return result.stdout.strip()


def read_sources() -> list[tuple[str, str]]:
    return parse_sources(_gsettings("get", SCHEMA, "sources"))


def write_sources(sources: list[tuple[str, str]]) -> None:
    # repr() provides valid GVariant tuple/list syntax for simple strings.
    _gsettings("set", SCHEMA, "sources", repr(sources) if sources else "@a(ss) []")


def apply_profile_layout(profile: str) -> str:
    """Explicit opt-in change; preserve all prior languages and backup original."""
    profile = validate(profile)
    original = read_sources()
    desired = prepend_layout(profile, original)
    if desired == original:
        return "This keyboard layout is already first in GNOME's input sources."

    backup = backup_path()
    if not backup.exists():
        # Exclusive creation ensures a prior backup is never silently replaced.
        backup.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"sources": original}, stream)
            stream.write("\n")
    write_sources(desired)
    return (
        f"GNOME now prefers {LAYOUT_IDS[profile]} as the first input source. "
        "Your previous sources were preserved; use Restore keyboard layout to undo. "
        "The ⌘ Command key normally sends Super on Apple keyboards; this layout "
        "change does not forcibly remap physical modifier keys."
    )


def restore_previous_layout() -> str:
    path = backup_path()
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
        values = saved["sources"]
        if not isinstance(values, list):
            raise ValueError("Malformed backup")
        sources = [tuple(item) for item in values]
        # Strict validation before writing anything to GNOME.
        parse_sources(repr(sources))
    except FileNotFoundError as exc:
        raise KeyboardError("No saved keyboard layout was found to restore") from exc
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise KeyboardError("The keyboard backup is invalid or unreadable") from exc
    write_sources(sources)
    path.unlink()
    return "Restored your previous GNOME keyboard layouts."
