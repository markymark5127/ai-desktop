"""Small, private audit trail for user-approved actions (not general chat logs)."""

from __future__ import annotations

import json
import os
import re
from collections import deque
from datetime import datetime, timezone
from pathlib import Path


def history_file() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    return base / "ai-desktop" / "actions.jsonl"


def record_action(tool: str, status: str) -> None:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", tool):
        raise ValueError("Invalid tool name")
    if status not in {"succeeded", "failed"}:
        raise ValueError("Invalid status")
    path = history_file()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "status": status,
    }
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, separators=(",", ":")) + "\n")


def recent_actions(limit: int = 20) -> list[dict[str, str]]:
    path = history_file()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as stream:
        lines = deque(stream, maxlen=max(1, min(limit, 100)))
    output = []
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and "tool" in item and "status" in item:
            output.append(item)
    return output
