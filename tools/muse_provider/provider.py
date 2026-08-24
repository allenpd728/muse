"""Pluggable LLM generation adapter.

generate(prompt) → dict. Providers:
- GeminiProvider: free-tier Gemini API (GOOGLE_API_KEY). Live calls only
  when explicitly enabled (tests never touch the network).
- ManualProvider: prints the prompt, reads pasted JSON from stdin — the
  no-key fallback (spike-era precedent).
- RecordedProvider: deterministic fixture replay for tests and CI.
"""

from __future__ import annotations

import json
import os
import urllib.request


class ProviderError(ValueError):
    """Generation failed (network, parse, empty response)."""


class Provider:
    name = "base"

    def generate(self, prompt: str) -> dict:
        raise NotImplementedError


class GeminiProvider(Provider):
    name = "gemini"
    # Free-tier model rot: 2.0/2.5 404, flash-latest 503s under load.
    # Working as of 2026-08-24; re-probe /v1beta/models if it 404s again.
    DEFAULT_MODEL = "gemini-3-flash-preview"

    def __init__(self, api_key=None, model=None, live=False, timeout=180):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.model = model or self.DEFAULT_MODEL
        self.live = live  # network calls only when live=True
        self.timeout = timeout  # full-DNA responses (100s of notes) are slow

    def generate(self, prompt: str) -> dict:
        if not self.live:
            raise ProviderError(
                "GeminiProvider is offline (live=False); use RecordedProvider "
                "for tests or pass live=True for a real call"
            )
        if not self.api_key:
            raise ProviderError("GOOGLE_API_KEY not set")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }).encode()
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.load(resp)
        except Exception as e:
            raise ProviderError(f"gemini call failed: {e}") from e
        try:
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise ProviderError(f"gemini response not structured JSON: {e}") from e


class ManualProvider(Provider):
    name = "manual"

    def __init__(self, input_fn=None, output_fn=None):
        self._input = input_fn or input
        self._output = output_fn or print

    def generate(self, prompt: str) -> dict:
        self._output("=== PROMPT (paste into your LLM) ===")
        self._output(prompt)
        self._output("=== END PROMPT — paste the JSON response below ===")
        text = self._input("response> ")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ProviderError(f"pasted response is not JSON: {e}") from e


class RecordedProvider(Provider):
    """Deterministic fixture replay: maps prompt hash → recorded response."""

    name = "recorded"

    def __init__(self, responses: dict):
        self.responses = responses

    def generate(self, prompt: str) -> dict:
        key = str(hash(prompt))
        if key not in self.responses:
            raise ProviderError(
                f"no recorded response for this prompt (hash {key}); "
                f"record one and add it to the fixture"
            )
        return self.responses[key]


def default_provider(live=False):
    """Gemini when a key exists and live=True; otherwise manual fallback."""
    if live and os.environ.get("GOOGLE_API_KEY"):
        return GeminiProvider(live=True)
    return ManualProvider()
