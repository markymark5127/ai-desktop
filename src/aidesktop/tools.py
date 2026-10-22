"""Deliberately limited Linux tools. Never run arbitrary model-generated shell."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Callable


class ToolError(Exception):
    pass


def _command(argv: list[str], timeout: int = 6) -> str:
    try:
        result = subprocess.run(
            argv, capture_output=True, text=True, check=False, timeout=timeout
        )
    except FileNotFoundError as exc:
        raise ToolError(f"Required utility is not installed: {argv[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ToolError(f"Utility timed out: {argv[0]}") from exc
    if result.returncode != 0:
        raise ToolError((result.stderr or "Command failed").strip()[:400])
    return (result.stdout.strip() or "(no output)")[:5000]


def _system_snapshot(_: dict[str, str]) -> str:
    usage = shutil.disk_usage("/")
    return (
        f"OS: {platform.system()} {platform.release()}\n"
        f"Architecture: {platform.machine()}\n"
        f"CPU threads: {os.cpu_count()}\n"
        f"Root filesystem free: {usage.free // (1024 ** 3)} GiB "
        f"of {usage.total // (1024 ** 3)} GiB"
    )


def _audio_outputs(_: dict[str, str]) -> str:
    return (
        "Audio outputs:\n"
        + _command(["pactl", "list", "short", "sinks"])
        + "\nCurrent default:\n"
        + _command(["pactl", "get-default-sink"])
    )


def _network_status(_: dict[str, str]) -> str:
    return _command(["nmcli", "-f", "DEVICE,TYPE,STATE", "device", "status"])


def _recent_warnings(_: dict[str, str]) -> str:
    return _command([
        "journalctl", "--user", "-p", "warning", "-n", "20",
        "--no-pager", "--output=short-iso",
    ])


def _installed_apps(_: dict[str, str]) -> str:
    return _command(["flatpak", "list", "--app", "--columns=application,name"])


def _launch_application(args: dict[str, str]) -> str:
    desktop_id = args["desktop_id"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,150}", desktop_id):
        raise ToolError("Invalid desktop application ID")
    try:
        subprocess.Popen(
            ["gtk-launch", desktop_id],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError as exc:
        raise ToolError("gtk-launch is not installed") from exc
    return f"Launch requested for {desktop_id}. App startup is not yet verified."


def _set_audio_output(args: dict[str, str]) -> str:
    sink = args["sink"]
    available = _command(["pactl", "list", "short", "sinks"])
    sinks = {line.split()[1] for line in available.splitlines() if len(line.split()) >= 2}
    if sink not in sinks:
        raise ToolError("Sink is not one of the currently detected audio devices")
    _command(["pactl", "set-default-sink", sink])
    actual = _command(["pactl", "get-default-sink"]).strip()
    if actual != sink:
        raise ToolError(f"Requested change was not verified. Current output: {actual}")
    return f"Confirmed default audio output is now {actual}."


@dataclass(frozen=True)
class Tool:
    description: str
    parameters: dict[str, str]
    requires_approval: bool
    handler: Callable[[dict[str, str]], str]


TOOLS: dict[str, Tool] = {
    "system_snapshot": Tool(
        "Read OS version, CPU thread count, and available root disk space", {}, False,
        _system_snapshot,
    ),
    "audio_outputs": Tool(
        "List current audio sinks and default output", {}, False, _audio_outputs,
    ),
    "network_status": Tool(
        "Show NetworkManager device states (not saved passwords)", {},
        False, _network_status,
    ),
    "recent_user_warnings": Tool(
        "Read up to 20 recent user-service warning logs (may contain personal data)",
        {}, False, _recent_warnings,
    ),
    "installed_apps": Tool(
        "List installed Flatpak applications", {}, False, _installed_apps,
    ),
    "launch_application": Tool(
        "Launch a desktop application by its desktop file ID",
        {"desktop_id": "Desktop file ID such as org.gnome.Calculator"},
        True, _launch_application,
    ),
    "set_audio_output": Tool(
        "Change the default audio sink to one of the sinks listed by audio_outputs",
        {"sink": "Exact existing sink name"}, True, _set_audio_output,
    ),
}


def run_tool(name: str, arguments: dict[str, str]) -> str:
    tool = TOOLS.get(name)
    if tool is None:
        raise ToolError(f"Unsupported tool: {name}")
    if not isinstance(arguments, dict):
        raise ToolError("Tool arguments must be an object")
    if set(arguments) != set(tool.parameters):
        raise ToolError(f"{name} requires exactly these arguments: {list(tool.parameters)}")
    if not all(isinstance(value, str) and len(value) <= 256 for value in arguments.values()):
        raise ToolError("Tool arguments must be strings no longer than 256 characters")
    return tool.handler(arguments)
