"""Headless Newelle GUI-API client, deliberately restricted to loopback inference.

The /v1/chat/completions route calls the configured LLM directly. Unlike
Newelle's /v2/chat/completions or /api/messages/run-llm it does not ask the
Newelle agent to execute terminal commands or MCP tools.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from .tools import ToolError


class NewelleError(ToolError):
    """A safe, user-readable Newelle connection or protocol error."""


def _endpoint() -> str:
    raw = os.environ.get("AIDESKTOP_NEWELLE_PORT", "8081")
    try:
        port = int(raw)
    except ValueError as exc:
        raise NewelleError("Newelle port must be a number") from exc
    if not 1 <= port <= 65535:
        raise NewelleError("Newelle port must be between 1 and 65535")
    # Fixed loopback host: do not follow an environment-controlled arbitrary URL.
    return f"http://127.0.0.1:{port}"


def _api_key() -> str:
    """Read from an environment override or a per-user private token file."""
    key = os.environ.get("AIDESKTOP_NEWELLE_API_KEY", "").strip()
    if not key:
        path = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "ai-desktop" / "newelle-token"
        try:
            key = path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise NewelleError("Could not read the Newelle API token file") from exc
    if not key or "\n" in key or "\r" in key:
        raise NewelleError(
            "Configure a Newelle GUI API key, then save the matching key in "
            "~/.config/ai-desktop/newelle-token (mode 0600). See README."
        )
    return key


def _request(path: str, payload: dict | None = None, *, timeout: int = 30) -> dict:
    if path not in ("/v1/models", "/v1/chat/completions"):
        raise NewelleError("Unsupported Newelle API endpoint")
    headers = {"Accept": "application/json"}
    headers["Authorization"] = f"Bearer {_api_key()}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = Request(
        _endpoint() + path,
        headers=headers,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        method="POST" if payload is not None else "GET",
    )
    # Never route loopback traffic through a proxy, including user-defined proxies.
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(1_000_001)
    except HTTPError as exc:
        if exc.code == 401:
            raise NewelleError(
                "Newelle rejected the API key. Configure AIDESKTOP_NEWELLE_API_KEY "
                "to match Newelle's GUI API settings."
            ) from exc
        raise NewelleError(f"Newelle returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise NewelleError(
            "Newelle is unavailable. Start its gui-api headless interface and "
            "check that it listens on 127.0.0.1 at the configured port."
        ) from exc
    if len(raw) > 1_000_000:
        raise NewelleError("Newelle response exceeded the allowed size")
    try:
        obj = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise NewelleError("Newelle sent invalid JSON") from exc
    if not isinstance(obj, dict):
        raise NewelleError("Newelle returned an unexpected response")
    return obj


def check_newelle() -> str:
    """Fast check for the expected API, without executing an AI request."""
    obj = _request("/v1/models", timeout=3)
    models = obj.get("data")
    if not isinstance(models, list):
        raise NewelleError("Connected service is not a compatible Newelle model API")
    names = [item["id"] for item in models if isinstance(item, dict) and isinstance(item.get("id"), str)]
    return "Newelle connected" + (f" · {names[0]}" if names else "")


def complete_newelle(system_prompt: str, user_prompt: str) -> str:
    """Inference only: model chooses tool *plans*; AI Desktop executes them."""
    if len(system_prompt) > 64_000 or len(user_prompt) > 48_000:
        raise NewelleError("Prompt is too large for the Newelle adapter")
    response = _request(
        "/v1/chat/completions",
        payload={
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        },
        timeout=90,
    )
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise NewelleError("Newelle returned no usable assistant response") from exc
    if not isinstance(content, str):
        raise NewelleError("Newelle returned an unsupported message format")
    if content.startswith("[Error:"):
        raise NewelleError("Newelle reported a model failure; check its provider settings")
    return content
