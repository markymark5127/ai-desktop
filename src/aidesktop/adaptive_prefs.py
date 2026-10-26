"""User preference for Mutsu Adaptive Desktop (2-in-1 tablet mode).

Writes the GNOME Shell extension setting when the schema is present.
Safe to call even if the extension is not installed.
"""
from __future__ import annotations

import subprocess

SCHEMA = "org.gnome.shell.extensions.mutsu-adaptive"
MODES = (
    ("Automatic", "automatic"),
    ("Always Desktop", "always-desktop"),
    ("Always Tablet", "always-tablet"),
)


def set_adaptive_mode(mode: str) -> str:
    """Set the Adaptive Desktop mode. Returns a user-facing status string."""
    if mode not in {value for _label, value in MODES}:
        return f"Unknown mode: {mode}"
    try:
        result = subprocess.run(
            ["gsettings", "set", SCHEMA, "mode", mode],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return f"Adaptive Desktop set to {mode}."
        err = (result.stderr or result.stdout or "").strip()
        if "No such schema" in err or "does not exist" in err:
            return (
                "Adaptive Desktop extension is not installed on this system. "
                "The choice was not saved."
            )
        return f"Could not set Adaptive Desktop mode: {err or 'unknown error'}"
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Could not set Adaptive Desktop mode: {exc}"


def get_adaptive_mode() -> str | None:
    """Return the current mode, or None if the extension is unavailable."""
    try:
        result = subprocess.run(
            ["gsettings", "get", SCHEMA, "mode"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip().strip("'")
    except (OSError, subprocess.TimeoutExpired):
        return None
