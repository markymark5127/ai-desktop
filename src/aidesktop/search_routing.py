"""Pure selection logic for local-first Spotlight plus explicit AI fallback.

Typing never sends data to an inference backend. Enter on the "Ask" row is
the only fallback, and known app matches take priority.
"""

from __future__ import annotations

from dataclasses import dataclass

from .search import AppResult, search_applications


QUESTION_STARTERS = frozenset({
    "ask", "why", "what", "how", "where", "when", "who", "can", "could",
    "would", "should", "please", "help", "fix", "troubleshoot", "explain",
    "install", "change", "set", "make", "turn", "is", "are", "do", "does",
})


@dataclass(frozen=True)
class SearchRoute:
    """App hits (if any) plus a named AI fallback; never an automatic request."""
    apps: tuple[AppResult, ...]
    offer_ai: bool
    query: str


def route_query(query: str, apps: list[AppResult], *, limit: int = 5) -> SearchRoute:
    query = query.strip()
    if not query:
        return SearchRoute((), False, "")
    lowered = query.casefold()
    if lowered.startswith("ask "):
        return SearchRoute((), True, query[4:].strip())
    if "?" in query or lowered.split()[0] in QUESTION_STARTERS:
        return SearchRoute((), True, query)
    target = query
    if lowered.startswith(("open ", "launch ")):
        target = query.split(" ", 1)[1].strip()
    results = search_applications(target, limit=limit, apps=apps) if target else []
    return SearchRoute(tuple(results), True, query)


def should_hide_on_focus_loss(
    *,
    activated_once: bool,
    is_active: bool,
    is_visible: bool,
    modal_dialog: bool,
    settings_open: bool,
) -> bool:
    """Prevent initial-window and in-app modal/popover focus races."""
    return (
        activated_once and is_visible and not is_active
        and not modal_dialog and not settings_open
    )


SHELL_EXTENSION = "mutsu-branding@mutsu-os"


def shell_manages_dismissal(enabled_extensions=None, disable_user_extensions=None) -> bool:
    """True when Mutsu's GNOME Shell extension owns hiding Search.

    The extension dismisses Search on taps outside it and on app switches,
    and ignores taps on the on-screen keyboard. A window only sees "lost
    focus", so it would close while the user types on the keyboard.
    """
    import os
    if os.environ.get("MUTSU_SEARCH_SELF_DISMISS") == "1":
        return False
    if enabled_extensions is None:
        try:
            from gi.repository import Gio
            source = Gio.SettingsSchemaSource.get_default()
            if source is None or source.lookup("org.gnome.shell", True) is None:
                return False
            settings = Gio.Settings.new("org.gnome.shell")
            enabled_extensions = list(settings.get_strv("enabled-extensions"))
            disable_user_extensions = settings.get_boolean("disable-user-extensions")
        except Exception:  # noqa: BLE001 - no GNOME Shell settings available
            return False
    return SHELL_EXTENSION in enabled_extensions and not disable_user_extensions
