"""Per-user first-run onboarding preferences, independent from GNOME/GTK.

Onboarding stores a user-controlled opt-in for sending questions/diagnostics
to configured local or cloud AI models. It NEVER grants model tool privileges
or permission for system-changing actions. The opt-in defaults to off.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

LEARNING_STYLES = (
    ("Just help me fix things", "simple"),
    ("Help me and briefly explain", "guided"),
    ("Teach me as we go", "learn"),
)
PHONE_OPTIONS = (
    ("iPhone", "iphone"),
    ("Android", "android"),
    ("I'll do this later", "later"),
)
STATES = {"pending", "completed", "skipped"}
MODEL_SHARING_LABEL = "Allow AI model sharing"

DEFAULTS = {
    "status": "pending",
    "learning_style": "guided",
    "phone": "later",
    "model_sharing": False,
}


def preferences_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "ai-desktop" / "onboarding.json"


def _validated(value: dict) -> dict[str, str | bool]:
    if not isinstance(value, dict):
        raise ValueError("Onboarding preferences must be an object")
    data = {**DEFAULTS, **value}
    valid = {
        "status": STATES,
        "learning_style": {key for _, key in LEARNING_STYLES},
        "phone": {key for _, key in PHONE_OPTIONS},
    }
    if set(data) != set(DEFAULTS):
        raise ValueError("Unknown onboarding preference")
    for key, allowed in valid.items():
        if not isinstance(data[key], str) or data[key] not in allowed:
            raise ValueError(f"Invalid onboarding option: {key}")
    if not isinstance(data["model_sharing"], bool):
        raise ValueError("Model sharing consent must be a boolean")
    return data


def load_preferences() -> dict[str, str | bool]:
    try:
        with preferences_path().open("r", encoding="utf-8") as stream:
            return _validated(json.load(stream))
    except (OSError, ValueError, TypeError):
        return DEFAULTS.copy()


def save_preferences(**updates: str | bool) -> dict[str, str | bool]:
    updated = _validated({**load_preferences(), **updates})
    path = preferences_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".onboarding-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(updated, stream)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return updated


def is_setup_done() -> bool:
    return load_preferences()["status"] in ("completed", "skipped")


def mark_setup_done(*, skipped: bool = False) -> None:
    save_preferences(status="skipped" if skipped else "completed")


def get_learning_style() -> str:
    return str(load_preferences()["learning_style"])


def model_sharing_allowed() -> bool:
    """Persistent, explicit permission to send content to a model.

    Older onboarding files lack this setting: they default to False.
    Malformed settings also fail closed. Merely selecting a provider never
    grants consent.
    """
    return load_preferences()["model_sharing"] is True


def set_model_sharing_allowed(allowed: bool) -> None:
    """Persist opt-in/opt-out before the UI claims the choice was saved."""
    if not isinstance(allowed, bool):
        raise ValueError("Model sharing consent must be a boolean")
    save_preferences(model_sharing=allowed)


def helper_intro(style: str) -> str:
    """Human-friendly text only; does not adjust tool execution behavior."""
    if style == "simple":
        return "I'll focus on the next useful step, ask before changing settings, and tell you what happened."
    if style == "guided":
        return "I'll explain the likely cause, suggest a safe fix, ask before changing settings, and check the result."
    if style == "learn":
        return (
            "I'll help investigate the problem, explain the Linux concepts with "
            "Mac comparisons, ask before changing settings, and show how to do it yourself."
        )
    raise ValueError("Unknown learning style")
