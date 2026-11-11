"""Tablet mode preference (Mutsu's adaptive GNOME Shell extension).

Ported from the old feature/adaptive-wizard-page branch. Writes the
extension's own setting; safe to call when the extension isn't there.
"""
from __future__ import annotations

import os
import subprocess

SCHEMA = "org.gnome.shell.extensions.mutsu-adaptive"
# The extension keeps its compiled schema in its own folder.
SCHEMA_DIRS = (
    "/usr/share/gnome-shell/extensions/mutsu-adaptive@mutsu-os/schemas",
    os.path.expanduser("~/.local/share/gnome-shell/extensions/mutsu-adaptive@mutsu-os/schemas"),
)
MODES = (
    ("Automatic (when a 2-in-1 folds)", "automatic"),
    ("Always desktop", "always-desktop"),
    ("Always tablet", "always-tablet"),
)


def _gsettings(*args: str) -> subprocess.CompletedProcess | None:
    schema_dir = next((d for d in SCHEMA_DIRS if os.path.isdir(d)), None)
    argv = ["gsettings"] + (["--schemadir", schema_dir] if schema_dir else []) + list(args)
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None


def set_adaptive_mode(mode: str) -> str:
    """Set the tablet mode choice. Returns a short status for the user."""
    if mode not in {value for _label, value in MODES}:
        return f"Unknown mode: {mode}"
    result = _gsettings("set", SCHEMA, "mode", mode)
    if result is None or result.returncode != 0:
        return "Tablet mode isn't available on this system; nothing was changed."
    label = next(label for label, value in MODES if value == mode)
    return f"Tablet mode: {label}."


def get_adaptive_mode() -> str | None:
    """The current choice, or None if the extension isn't there."""
    result = _gsettings("get", SCHEMA, "mode")
    if result is None or result.returncode != 0:
        return None
    value = result.stdout.strip().strip("'")
    return value if value in {v for _l, v in MODES} else None
