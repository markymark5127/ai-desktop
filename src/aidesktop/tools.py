"""Deliberately limited Linux tools. Never run arbitrary model-generated shell."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Callable

from .search import resolve_app_id, search_applications


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
    if not resolve_app_id(desktop_id):
        raise ToolError("Application is not installed or is not visible in the app menu")
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


def _search_installed_apps(args: dict[str, str]) -> str:
    matches = search_applications(args["query"], limit=8)
    if not matches:
        return "No installed applications found for that search."
    return "\n".join(f"{app.name}: {app.desktop_id}" for app in matches)


def _repair_path():
    from pathlib import Path
    import os
    root = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state") / "ai-desktop"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root / "last-repair.json"


def _audio_evidence() -> dict[str, str]:
    return {
        "default_sink": _command(["pactl", "get-default-sink"]).strip(),
        "sinks": _command(["pactl", "list", "short", "sinks"]).strip(),
        "pipewire": _command(["systemctl", "--user", "is-active", "pipewire"]).strip(),
        "wireplumber": _command(["systemctl", "--user", "is-active", "wireplumber"]).strip(),
    }


def _audio_repair(args: dict[str, str]) -> str:
    """Transaction: evidence, restart, verify, store an executable undo."""
    import json
    before = _audio_evidence()
    if not before["default_sink"]:
        raise ToolError("No default audio sink was found, so there is nothing safe to restart")
    _command(["systemctl", "--user", "restart", "pipewire", "pipewire-pulse", "wireplumber"], timeout=15)
    after = _audio_evidence()
    if not after["default_sink"]:
        raise ToolError("Audio restart finished but no default sink was verified")
    if after["pipewire"] != "active" or after["wireplumber"] != "active":
        raise ToolError(f"Audio services did not come back active: {after}")
    record = {
        "kind": "audio_restart",
        "before_sink": before["default_sink"],
        "after_sink": after["default_sink"],
    }
    path = _repair_path()
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return (
        f"Audio repair applied. Before: sink {before['default_sink']}, "
        f"pipewire {before['pipewire']}, wireplumber {before['wireplumber']}. "
        f"After: sink {after['default_sink']}, pipewire {after['pipewire']}, "
        f"wireplumber {after['wireplumber']}. Undo is available as undo_last_repair."
    )


def _undo_last_repair(_: dict[str, str]) -> str:
    import json
    path = _repair_path()
    if not path.exists():
        raise ToolError("No repair is recorded to undo")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("kind") != "audio_restart":
        raise ToolError("The last repair is not an audio change")
    sink = record.get("before_sink") or ""
    available = _command(["pactl", "list", "short", "sinks"])
    sinks = {line.split()[1] for line in available.splitlines() if len(line.split()) >= 2}
    if sink not in sinks:
        raise ToolError(f"Previous sink {sink} is no longer present, so undo was not applied")
    _command(["pactl", "set-default-sink", sink])
    actual = _command(["pactl", "get-default-sink"]).strip()
    if actual != sink:
        raise ToolError(f"Undo was not verified. Current output: {actual}")
    path.unlink(missing_ok=True)
    return f"Undid the audio repair. Default sink is {actual} again."


def _bluetooth_status(_: dict[str, str]) -> str:
    return _command(["bluetoothctl", "show"])


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
    "search_installed_apps": Tool(
        "Find installed applications using a friendly name. Returns launchable desktop IDs.",
        {"query": "Name or part of an application name"}, False, _search_installed_apps,
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
    "audio_repair": Tool(
        "Restart user audio, verify services and the default sink, and store an undo.",
        {}, True, _audio_repair,
    ),
    "undo_last_repair": Tool(
        "Undo the last approved audio repair by restoring the previous default sink.",
        {}, True, _undo_last_repair,
    ),
    "bluetooth_status": Tool(
        "Show the Bluetooth adapter state. Read-only evidence before any pairing change.",
        {}, False, _bluetooth_status,
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
