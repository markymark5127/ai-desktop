"""Mutsu Search settings, for Settings → Mutsu Search.

GNOME Settings shows the page; this module is the one place that reads and
writes the settings, so Search, the welcome wizard and Settings agree:

    python3 -m aidesktop.search_settings get
    python3 -m aidesktop.search_settings set <key> <value>
    python3 -m aidesktop.search_settings test-ai

Each command prints one JSON object. Keys: provider, ai_enabled,
cloud_allowed, search_engine, theme. Nothing here grants an AI permission
to change the system; that stays behind Search's own approval step.
"""

from __future__ import annotations

import json
import sys

from .keyboard_profiles import get_profile, shortcut_label
from .onboarding import (
    PROVIDERS, CLOUD_PROVIDERS, load_preferences, save_preferences,
    set_model_sharing_allowed, set_cloud_sharing_allowed,
)
from .spotlight import SEARCH_ENGINES
from .themes import THEME_LABELS, load_theme, save_theme

PROVIDER_LABELS = {
    "newelle": "Mutsu Mechanic (on this computer)",
    "builtin": "Built-in (offline)",
    "local": "Local Ollama",
    "openai": "OpenAI API",
    "anthropic": "Claude API",
}
THEMES = [name for _label, name in THEME_LABELS]


def snapshot() -> dict:
    prefs = load_preferences()
    return {
        "provider": prefs["provider"],
        "providers": [[key, PROVIDER_LABELS[key]] for key in PROVIDERS],
        "cloud_providers": sorted(CLOUD_PROVIDERS),
        "ai_enabled": prefs["ai_enabled"] is True,
        "cloud_allowed": prefs["model_sharing"] is True,
        "search_engine": prefs["search_engine"],
        "search_engines": [[key, label] for key, (label, _url) in SEARCH_ENGINES.items()],
        "theme": load_theme(),
        "themes": [[name, label] for label, name in THEME_LABELS],
        "shortcut": shortcut_label(get_profile()),
    }


def _bool(value: str) -> bool:
    lowered = str(value).strip().lower()
    if lowered in ("1", "true", "yes", "on"):
        return True
    if lowered in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"not a true/false value: {value!r}")


def apply(key: str, value: str) -> dict:
    """Save one setting; returns the new snapshot plus an optional message."""
    message = ""
    if key == "provider":
        if value not in PROVIDERS:
            raise ValueError(f"unknown provider: {value!r}")
        save_preferences(provider=value)
        if value in CLOUD_PROVIDERS and not load_preferences()["model_sharing"]:
            message = "Turn on cloud AI models to send questions to this provider."
    elif key == "ai_enabled":
        set_model_sharing_allowed(_bool(value))
    elif key == "cloud_allowed":
        set_cloud_sharing_allowed(_bool(value))
    elif key == "search_engine":
        if value not in SEARCH_ENGINES:
            raise ValueError(f"unknown search engine: {value!r}")
        save_preferences(search_engine=value)
    elif key == "theme":
        if value not in THEMES:
            raise ValueError(f"unknown theme: {value!r}")
        save_theme(value)
        try:
            from .wallpaper import WallpaperError, apply_theme_wallpaper
            try:
                message = apply_theme_wallpaper(value)
            except WallpaperError as exc:
                message = f"Search uses the new look. The wallpaper stayed the same: {exc}"
        except ImportError:  # no GNOME bindings (tests, headless)
            pass
    else:
        raise ValueError(f"unknown setting: {key!r}")
    return {**snapshot(), "message": message}


def test_ai() -> dict:
    if not load_preferences()["ai_enabled"]:
        return {"ok": False, "message": "Turn on Mutsu Mechanic AI first."}
    from .newelle_client import NewelleError, test_newelle
    try:
        return {"ok": True, "message": test_newelle()}
    except NewelleError as exc:
        return {"ok": False, "message": f"Mutsu Mechanic isn't ready: {exc}"}


def main(argv: list[str]) -> int:
    try:
        if len(argv) == 2 and argv[1] == "get":
            result = snapshot()
        elif len(argv) == 4 and argv[1] == "set":
            result = apply(argv[2], argv[3])
        elif len(argv) == 2 and argv[1] == "test-ai":
            result = test_ai()
        else:
            print(__doc__, file=sys.stderr)
            return 2
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
