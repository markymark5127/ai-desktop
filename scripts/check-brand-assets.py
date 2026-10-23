#!/usr/bin/env python3
"""Report Mutsu OS branding assets available for user and system-image work.

Read-only: never mutates GNOME, /usr, boot, GDM, or Bazzite's existing files.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "assets" / "icons"
WALLPAPER_DIR = ROOT / "assets" / "wallpapers"

REQUIRED = {
    "mutsu-logo-symbol.svg": "Primary Mutsu emblem (About/launcher/boot source)",
    "mutsu-logo-symbolic.svg": "Single-color icon (top bar and GNOME symbolic UI)",
    "mutsu-logo-wordmark.svg": "Horizontal Mutsu OS text+symbol (GDM/login)",
}
OPTIONAL = {
    "mutsu-logo-original.svg": "Original black logo",
    "mutsu-logo-japandi.svg": "Sage Calm/Japandi mark",
    "mutsu-logo-cyberpunk.svg": "Neon Cyberpunk gradient mark",
    "mutsu-wordmark-japandi.svg": "Sage horizontal wordmark",
    "mutsu-wordmark-cyberpunk.svg": "Cyberpunk horizontal wordmark",
    "mutsu-logo-symbolic-white.svg": "White-on-dark symbolic mark (optional)",
    "mutsu-ai.svg": "Custom Mutsu AI suggestion icon",
    "mutsu-app-grid.svg": "Tablet home/app-grid icon",
}
WALLPAPERS = {
    "mutsu-japandi-4k.png": "Calm/Japandi desktop background",
    "mutsu-cyberpunk-4k.png": "Cyberpunk desktop background",
}


def valid_svg(path: Path) -> tuple[bool, str]:
    if not path.is_file() or path.stat().st_size == 0:
        return False, "missing"
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        return False, f"invalid SVG ({exc})"
    if root.tag not in ("{http://www.w3.org/2000/svg}svg", "svg"):
        return False, "not an SVG root element"
    return True, "ready"


def audit() -> tuple[list[str], int]:
    lines = ["Mutsu OS asset inventory", "=" * 26]
    missing_required = 0
    for header, directory, items in (
        ("Required vector artwork", ICON_DIR, REQUIRED),
        ("Optional vector artwork", ICON_DIR, OPTIONAL),
    ):
        lines.append(f"\n{header}  ({directory.relative_to(ROOT)}/)")
        for name, purpose in items.items():
            ok, status = valid_svg(directory / name)
            if name in REQUIRED and not ok:
                missing_required += 1
            lines.append(f"  [{'OK' if ok else '--'}] {name}: {purpose} [{status}]")
    lines.append("\nWallpaper files")
    for name, purpose in WALLPAPERS.items():
        path = WALLPAPER_DIR / name
        present = path.is_file() and path.stat().st_size > 0
        lines.append(f"  [{'OK' if present else '--'}] {name}: {purpose}")
    if ICON_DIR.is_dir():
        extras = sorted(
            item.name for item in ICON_DIR.glob("*.svg")
            if item.name not in REQUIRED and item.name not in OPTIONAL
        )
        if extras:
            lines.extend(["\nOther SVG names present (review and rename if appropriate):"] +
                         ["  " + item for item in extras])
    lines.append(
        "\nThis is an inventory only. User icons are not installed by this command."
    )
    return lines, missing_required


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Mutsu OS branding assets")
    parser.add_argument("--strict", action="store_true",
                        help="Exit nonzero until the three core SVGs are uploaded")
    args = parser.parse_args()
    lines, missing = audit()
    print("\n".join(lines))
    return 1 if args.strict and missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
