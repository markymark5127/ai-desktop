"""Public product labels for the Mutsu OS GNOME prototype.

Keep user-facing product names independent of legacy technical identifiers.
The `aidesktop` Python module, `ai-desktop` command/config directories and
`io.github.markymark5127.AIDesktop` application ID intentionally remain
stable during the branding transition, protecting installed launchers,
saved preferences, shortcut backups, Newelle keys, and user services.
"""

PRODUCT_NAME = "Mutsu OS"
SEARCH_NAME = f"{PRODUCT_NAME} Search"
AI_NAME = "Mutsu Mechanic"
WELCOME_TITLE = f"Welcome to {PRODUCT_NAME}"

from pathlib import Path


def icon_source(*filenames: str) -> Path | None:
    """Find an uploaded owner-supplied SVG; never fetch icons over the network.

    Search the repo first for development, then installed system/share
    locations for future Mutsu OS image packaging.
    """
    root = Path(__file__).resolve().parents[2]
    folders = (
        root / "assets" / "icons",
        Path("/usr/share/pixmaps/mutsu"),
        Path("/usr/share/icons/hicolor/scalable/apps"),
    )
    for filename in filenames:
        if not filename.endswith(".svg") or "/" in filename or "\\" in filename:
            continue
        for folder in folders:
            candidate = folder / filename
            if candidate.is_file() and candidate.stat().st_size > 0:
                return candidate
    return None
