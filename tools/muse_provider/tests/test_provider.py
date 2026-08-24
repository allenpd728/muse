"""Provider adapter tests (issue #207). No live API calls."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from muse_provider import (  # noqa: E402
    GeminiProvider,
    ManualProvider,
    ProviderError,
    RecordedProvider,
    default_provider,
)


def test_recorded_provider_replays():
    p = RecordedProvider({str(hash("prompt a")): {"mockup": True}})
    assert p.generate("prompt a") == {"mockup": True}


def test_recorded_provider_fails_loudly_on_unknown_prompt():
    p = RecordedProvider({})
    with pytest.raises(ProviderError, match="no recorded response"):
        p.generate("unrecorded")


def test_gemini_offline_by_default():
    p = GeminiProvider(api_key="x", live=False)
    with pytest.raises(ProviderError, match="offline"):
        p.generate("anything")


def test_gemini_requires_key_when_live(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    p = GeminiProvider(api_key=None, live=True)
    with pytest.raises(ProviderError, match="GOOGLE_API_KEY"):
        p.generate("anything")


def test_manual_provider_reads_pasted_json():
    captured = []
    p = ManualProvider(
        input_fn=lambda _: '{"ok": true}',
        output_fn=captured.append,
    )
    assert p.generate("the prompt") == {"ok": True}
    assert any("the prompt" in c for c in captured)


def test_manual_provider_rejects_non_json():
    p = ManualProvider(input_fn=lambda _: "not json", output_fn=lambda _: None)
    with pytest.raises(ProviderError, match="not JSON"):
        p.generate("x")


def test_default_provider_falls_back_to_manual():
    os.environ.pop("GOOGLE_API_KEY", None)
    p = default_provider(live=False)
    assert isinstance(p, ManualProvider)


def test_default_provider_gemini_when_live_and_keyed():
    os.environ["GOOGLE_API_KEY"] = "test-key"
    p = default_provider(live=True)
    assert isinstance(p, GeminiProvider)
    del os.environ["GOOGLE_API_KEY"]
