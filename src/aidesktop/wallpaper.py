"""Reversible, explicitly requested GNOME wallpaper switching for Mutsu OS.

Only a user selecting an appearance theme triggers GNOME settings changes.
First startup never overrides an existing user's wallpaper. Theme assets stay
in the repository during prototyping and will be installed by the distro later.
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


WALLPAPER_NAMES = {
    "japandi": "mutsu-japandi-4k.png",
    "cyberpunk": "mutsu-cyberpunk-4k.png",
}
SCHEMA = "org.gnome.desktop.background"
KEYS = ("picture-uri", "picture-uri-dark")


class WallpaperError(RuntimeError):
    """Wallpaper change was not applied; app palette can still be used."""


def _state_path() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    return base / "ai-desktop" / "previous-wallpaper.json"


def find_wallpaper(theme: str) -> Path:
    if theme not in WALLPAPER_NAMES:
        raise WallpaperError("Unknown Mutsu wallpaper theme")
    filename = WALLPAPER_NAMES[theme]
    repo = Path(__file__).resolve().parents[2]
    candidates = (
        repo / "assets" / "wallpapers" / filename,
        Path("/usr/share/backgrounds/mutsu") / filename,
        Path.home() / ".local/share/backgrounds/mutsu" / filename,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise WallpaperError(
        f"Missing {filename}. Pull the assets in assets/wallpapers/ first."
    )


def _get(key: str) -> str:
    try:
        result = subprocess.run(
            ["gsettings", "get", SCHEMA, key],
            capture_output=True, text=True, timeout=5, check=True,
        )
        value = ast.literal_eval(result.stdout.strip())
        if not isinstance(value, str):
            raise WallpaperError(f"Unexpected GNOME wallpaper value for {key}")
        return value
    except (OSError, ValueError, SyntaxError, subprocess.SubprocessError) as exc:
        raise WallpaperError(
            "Cannot read GNOME wallpaper preference; is this a GNOME session?"
        ) from exc


def _set(key: str, value: str) -> None:
    try:
        subprocess.run(
            ["gsettings", "set", SCHEMA, key, value],
            capture_output=True, text=True, timeout=5, check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise WallpaperError(
            f"Could not update GNOME wallpaper {key} (may be locked by policy)."
        ) from exc


def _read_state() -> dict | None:
    try:
        state = json.loads(_state_path().read_text(encoding="utf-8"))
        if not (
            isinstance(state, dict)
            and isinstance(state.get("previous"), dict)
            and isinstance(state.get("last_applied"), str)
            and all(isinstance(state["previous"].get(k), str) for k in KEYS)
        ):
            return None
        return state
    except (OSError, ValueError, TypeError):
        return None


def _write_state(state: dict) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(prefix=".wallpaper-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(state, output)
            output.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def apply_theme_wallpaper(theme: str) -> str:
    """Apply a selected theme wallpaper or restore on System.

    Before the first user-requested theme change, save both GNOME background
    values. If user manually changes their wallpaper later, do not overwrite
    their edits when switching back to System. Never run at app startup.
    """
    if theme not in (*WALLPAPER_NAMES, "system"):
        raise WallpaperError("Unsupported appearance theme")
    if not shutil.which("gsettings"):
        raise WallpaperError("GNOME gsettings is not installed")
    state = _read_state()
    current = {key: _get(key) for key in KEYS}
    if theme == "system":
        if state is None:
            return "System appearance selected; no Mutsu wallpaper backup exists."
        if not all(current[k] == state["last_applied"] for k in KEYS):
            # Respect changes performed manually since the last Mutsu selection.
            return "System appearance selected; keeping your manually changed wallpaper."
        try:
            for key in KEYS:
                _set(key, state["previous"][key])
        except WallpaperError:
            for key in KEYS:
                try:
                    _set(key, current[key])
                except WallpaperError:
                    pass
            raise
        _state_path().unlink(missing_ok=True)
        return "Restored the previous GNOME wallpaper."

    uri = find_wallpaper(theme).resolve().as_uri()
    if state is None:
        state = {"previous": current, "last_applied": uri}
    else:
        state["last_applied"] = uri
    # Save the prior values before touching GNOME settings, so recovery works.
    _write_state(state)
    try:
        for key in KEYS:
            _set(key, uri)
    except WallpaperError:
        for key in KEYS:
            try:
                _set(key, current[key])
            except WallpaperError:
                pass
        raise
    return f"Applied the Mutsu {theme.title()} wallpaper."
