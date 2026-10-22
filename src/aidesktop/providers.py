"""Pluggable inference adapters; no provider SDK required for the prototype.

Cloud prompts and tool outputs leave the machine only after consent in the UI.
ChatGPT and Claude subscriptions are not interchangeable with API credentials.
"""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(Exception):
    pass


def _post_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            return json.loads(response.read(2_000_000))
    except HTTPError as exc:
        raise ProviderError(f"Provider returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise ProviderError("Could not reach provider; check connection and credentials") from exc
    except (ValueError, KeyError, TypeError) as exc:
        raise ProviderError("Provider returned an invalid response") from exc


def complete(provider: str, system_prompt: str, user_prompt: str) -> str:
    if provider == "local":
        model = os.getenv("AIDESKTOP_LOCAL_MODEL", "qwen2.5:3b")
        data = _post_json(
            "http://127.0.0.1:11434/api/chat",
            {
                "model": model, "stream": False, "format": "json",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            {},
        )
        return str(data["message"]["content"])

    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ProviderError("Set OPENAI_API_KEY for OpenAI API (separate API billing)")
        data = _post_json(
            "https://api.openai.com/v1/chat/completions",
            {
                "model": os.getenv("AIDESKTOP_OPENAI_MODEL", "gpt-4.1-mini"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            {"Authorization": f"Bearer {key}"},
        )
        return str(data["choices"][0]["message"]["content"])

    if provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ProviderError("Set ANTHROPIC_API_KEY for Claude API (separate API billing)")
        data = _post_json(
            "https://api.anthropic.com/v1/messages",
            {
                "model": os.getenv("AIDESKTOP_ANTHROPIC_MODEL", "claude-sonnet-4-5"),
                "max_tokens": 700,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            {"x-api-key": key, "anthropic-version": "2023-06-01"},
        )
        return "\n".join(
            part.get("text", "") for part in data["content"] if part.get("type") == "text"
        )

    raise ProviderError(f"Unsupported model provider: {provider}")
