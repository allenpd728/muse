"""muse_stream — S1 event-stream format tooling (golden vectors)."""

from .golden import canonical_json, generate, verify, work_to_canonical

__all__ = ["work_to_canonical", "canonical_json", "generate", "verify"]
