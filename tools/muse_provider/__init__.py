"""muse_provider — L1.2 pluggable LLM generation adapter (issue #207).

One interface: generate(prompt) → structured JSON. Gemini free-tier first
(spike-era precedent), manual-paste fallback when no key exists. Stock
swappable model steered by prompt — no training (locked decision). Tests
use recorded fixtures only; no live API calls.
"""

from .provider import (
    GeminiProvider,
    ManualProvider,
    Provider,
    ProviderError,
    RecordedProvider,
    default_provider,
)

__all__ = [
    "GeminiProvider",
    "ManualProvider",
    "Provider",
    "ProviderError",
    "RecordedProvider",
    "default_provider",
]
