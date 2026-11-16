"""LLM backend. Uses the Anthropic Messages API over HTTPS with stdlib only."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-5-5"


class Brain:
    def __init__(self, system_prompt: str, api_key: str | None = None, model: str | None = None,
                 timeout: float = 60.0) -> None:
        self.system_prompt = system_prompt
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or os.environ.get("JARVIS_MODEL", DEFAULT_MODEL)
        self.timeout = timeout
        self.history: list[dict] = []
        self.max_history = 20

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def ask(self, message: str) -> str:
        if not self.available:
            return ("I am running without a language model, sir. Set ANTHROPIC_API_KEY to enable "
                    "open-ended conversation. Local skills such as time, math, and notes still work.")

        self.history.append({"role": "user", "content": message})
        self.history = self.history[-self.max_history:]
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": self.system_prompt,
            "messages": self.history,
        }
        request = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode(),
            headers={
                "content-type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": API_VERSION,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read())
        except urllib.error.HTTPError as err:
            self.history.pop()
            return f"The language service returned an error, sir ({err.code})."
        except (urllib.error.URLError, TimeoutError):
            self.history.pop()
            return "I cannot reach the language service at present, sir."

        reply = "".join(block.get("text", "") for block in body.get("content", [])
                        if block.get("type") == "text").strip() or "I have nothing to add, sir."
        self.history.append({"role": "assistant", "content": reply})
        return reply
