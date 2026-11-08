"""GSConnect (KDE Connect for GNOME) helpers for the welcome wizard.

Turns the extension on, lists the phones it can see, and asks one to pair.
Everything goes through GNOME's own tools and GSConnect's D-Bus API: no
network access of our own, nothing installed.
"""

from __future__ import annotations

import socket
import subprocess

GSCONNECT_ID = "gsconnect@andyholmes.github.io"
BUS_NAME = "org.gnome.Shell.Extensions.GSConnect"
OBJECT_PATH = "/org/gnome/Shell/Extensions/GSConnect"
DEVICE_IFACE = "org.gnome.Shell.Extensions.GSConnect.Device"


def enable_gsconnect(run=subprocess.run) -> tuple[bool, str]:
    """Turn GSConnect on. Returns (ok, message for the user)."""
    try:
        info = run(["gnome-extensions", "info", GSCONNECT_ID],
                   check=False, capture_output=True, text=True, timeout=5)
        if info.returncode != 0:
            return False, ("GSConnect isn't installed on this system, so phone "
                           "pairing isn't available here.")
        result = run(["gnome-extensions", "enable", GSCONNECT_ID],
                     check=False, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return False, "Couldn't reach GNOME's extension settings in this session."
    if result.returncode != 0:
        return False, "GNOME didn't turn GSConnect on. You can switch it on in Extensions."
    return True, "Phone connection is on. Your computer is now visible to KDE Connect."


def computer_name() -> str:
    """The name the phone will show for this computer."""
    try:
        out = subprocess.run(
            ["gsettings", "get", "org.gnome.Shell.Extensions.GSConnect", "name"],
            check=False, capture_output=True, text=True, timeout=3,
        ).stdout.strip().strip("'")
        if out:
            return out
    except (OSError, subprocess.TimeoutExpired):
        pass
    return socket.gethostname() or "this computer"


def parse_devices(managed: dict) -> list[dict]:
    """Phones from GSConnect's ObjectManager.GetManagedObjects() result
    ({path: {interface: {property: value}}}), paired ones first."""
    devices = []
    for path, interfaces in (managed or {}).items():
        props = interfaces.get(DEVICE_IFACE) if isinstance(interfaces, dict) else None
        if not isinstance(props, dict):
            continue
        devices.append({
            "path": path,
            "name": str(props.get("Name") or "Unknown device"),
            "type": str(props.get("Type") or "phone"),
            "paired": bool(props.get("Paired")),
            "connected": bool(props.get("Connected")),
        })
    devices.sort(key=lambda d: (not d["paired"], not d["connected"], d["name"].casefold()))
    return devices


def device_state(device: dict) -> str:
    if device["paired"] and device["connected"]:
        return "Paired and connected"
    if device["paired"]:
        return "Paired · not nearby right now"
    if device["connected"]:
        return "Found · not paired yet"
    return "Seen before · not reachable"


def pairing_steps(phone: str, name: str) -> list[str]:
    """What to do on the phone, in order."""
    steps = [
        "Scan the code above with your phone's camera and install KDE Connect.",
        "Connect your phone to the same Wi-Fi network as this computer.",
    ]
    if phone == "iphone":
        steps.append("Open KDE Connect. When iOS asks to find devices on your local "
                     "network, tap Allow.")
    else:
        steps.append("Open KDE Connect and allow the permissions it asks for "
                     "(you can skip any you don't want).")
    steps += [
        f"Tap “{name}” in the list of available devices, then Request pairing.",
        "Back here, your phone shows up below: tap Pair (or accept the pairing "
        "notification) to finish.",
    ]
    return steps


def list_devices(bus) -> list[dict]:
    """Ask GSConnect (via a Gio.DBusConnection) which phones it knows."""
    from gi.repository import GLib, Gio
    reply = bus.call_sync(BUS_NAME, OBJECT_PATH, "org.freedesktop.DBus.ObjectManager",
                          "GetManagedObjects", None, GLib.VariantType("(a{oa{sa{sv}}})"),
                          Gio.DBusCallFlags.NONE, 3000, None)
    return parse_devices(reply.unpack()[0])


def pair(bus, path: str) -> None:
    """Accept a phone's pairing request, or send one to it."""
    from gi.repository import GLib, Gio
    bus.call_sync(BUS_NAME, path, "org.gtk.Actions", "Activate",
                  GLib.Variant("(sava{sv})", ("pair", [], {})), None,
                  Gio.DBusCallFlags.NONE, 3000, None)
