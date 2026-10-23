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
