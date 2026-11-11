"""Plain logic for the welcome wizard's extra steps (Wi-Fi, AI and privacy,
backups), kept out of the GTK code so it can be tested."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

BACKUP_APP_ID = "org.gnome.DejaDup"
ALPHA_NOTICE = (
    "This is a developer alpha. Expect rough edges, and keep a copy of anything important. "
    "If something breaks, ask Mutsu Mechanic (Super+Space) or report it on GitHub."
)

PRIVACY_POINTS = (
    ("The AI runs on this computer.",
     "Mutsu Search and Mechanic use a model stored on your drive. Questions and answers "
     "don't leave the computer, and no account is needed."),
    ("Mechanic only looks when you ask.",
     "When you ask it to fix something it reads system logs and settings, and it tells you "
     "before it changes anything."),
    ("Nothing is collected.",
     "Mutsu OS sends no usage data. Updates are downloaded from GitHub's container registry."),
)


def wifi_name(run=subprocess.run) -> str | None:
    """The Wi-Fi network in use, if any (NetworkManager)."""
    if not shutil.which("nmcli"):
        return None
    try:
        result = run(["nmcli", "-t", "-f", "ACTIVE,SSID", "device", "wifi"],
                     capture_output=True, text=True, timeout=4, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    for line in (result.stdout or "").splitlines():
        active, _, ssid = line.partition(":")
        if active == "yes" and ssid:
            return ssid.replace("\\:", ":")
    return None


def connection_summary(online: bool, ssid: str | None) -> str:
    if online and ssid:
        return f"Connected to {ssid}."
    if online:
        return "You're online."
    return "Not connected. Choose a Wi-Fi network to get updates and apps."


def backup_app_installed(desktop_dirs=None) -> bool:
    dirs = desktop_dirs or (
        Path.home() / ".local/share/flatpak/exports/share/applications",
        Path("/var/lib/flatpak/exports/share/applications"),
        Path("/usr/share/applications"),
    )
    return any((Path(d) / f"{BACKUP_APP_ID}.desktop").exists() for d in dirs)
