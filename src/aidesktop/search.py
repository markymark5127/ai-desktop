"""Fast, model-free application search using freedesktop desktop entries.

Only desktop identifiers from actual application directories are returned. We do
not parse or run Exec= lines; launching belongs to the desktop environment.
"""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppResult:
    desktop_id: str
    name: str
    description: str = ""
    icon: str = "application-x-executable"


def application_dirs() -> list[Path]:
    """Directories ordered by freedesktop precedence, plus Flatpak exports."""
    home = Path.home()
    xdg_home = Path(os.environ.get("XDG_DATA_HOME") or home / ".local/share")
    xdg_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    bases = [xdg_home, *(Path(item) for item in xdg_dirs if item)]
    bases += [home / ".local/share/flatpak/exports/share", Path("/var/lib/flatpak/exports/share")]
    result = []
    for base in bases:
        directory = base / "applications"
        if directory not in result:
            result.append(directory)
    return result


def _parse(path: Path, desktop_id: str) -> AppResult | None:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            parser.read_file(handle)
    except (OSError, configparser.Error):
        return None
    if not parser.has_section("Desktop Entry"):
        return None
    info = parser["Desktop Entry"]
    if info.get("Type", "Application") != "Application":
        return None
    if info.get("Hidden", "false").lower() == "true" or info.get("NoDisplay", "false").lower() == "true":
        return None
    current = set(os.environ.get("XDG_CURRENT_DESKTOP", "").upper().split(":")) - {""}
    allowed = {name.upper() for name in info.get("OnlyShowIn", "").split(";") if name}
    denied = {name.upper() for name in info.get("NotShowIn", "").split(";") if name}
    if allowed and not current.intersection(allowed):
        return None
    if current.intersection(denied):
        return None
    name = info.get("Name", "").strip()
    if not name:
        return None
    return AppResult(desktop_id, name, info.get("Comment", "").strip(), info.get("Icon", "application-x-executable"))


def list_applications(directories: list[Path] | None = None) -> list[AppResult]:
    """Read app metadata, respecting the first entry with each desktop ID."""
    apps: list[AppResult] = []
    seen: set[str] = set()
    for directory in application_dirs() if directories is None else directories:
        if not directory.is_dir():
            continue
        try:
            paths = sorted(directory.rglob("*.desktop"))
        except OSError:
            continue
        for path in paths:
            desktop_id = str(path.relative_to(directory)).replace("/", "-")
            if desktop_id in seen:
                continue
            seen.add(desktop_id)
            app = _parse(path, desktop_id)
            if app:
                apps.append(app)
    return sorted(apps, key=lambda item: item.name.casefold())


def _score(query: str, app: AppResult) -> int:
    query = query.casefold().strip()
    name = app.name.casefold()
    desktop_id = app.desktop_id.casefold()
    description = app.description.casefold()
    if not query:
        return 1
    if query == name or query == desktop_id.removesuffix(".desktop"):
        return 100
    if name.startswith(query):
        return 85
    if any(token.startswith(query) for token in name.split()):
        return 70
    if query in name:
        return 60
    if query in desktop_id:
        return 45
    if query in description:
        return 25
    terms = query.split()
    if len(terms) > 1 and all(any(word.startswith(term) for word in name.split()) for term in terms):
        return 50
    return 0


def search_applications(query: str, *, limit: int = 8, apps: list[AppResult] | None = None) -> list[AppResult]:
    catalog = list_applications() if apps is None else apps
    matches = [(_score(query, app), app) for app in catalog]
    matches = [(score, app) for score, app in matches if score]
    matches.sort(key=lambda pair: (-pair[0], pair[1].name.casefold()))
    return [app for _, app in matches[:max(0, min(limit, 50))]]


def resolve_app_id(app_id: str, apps: list[AppResult] | None = None) -> bool:
    """True only when the ID belongs to a currently visible installed app."""
    catalog = list_applications() if apps is None else apps
    return any(item.desktop_id == app_id for item in catalog)
