"""C2 propose_seed: structured output + validation loop.

The LLM-emulated proposer is deterministic in v0: era from provenance or
inferred work properties, tempo bounds from delta-analysis budgets, form
structure from W3's pattern analyzer, assertions derived from analysis.
Human review approves each iteration.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class AuthorError(Exception):
    """Raised when proposed seed exceeds bounded retries."""


@dataclass
class Proposal:
    seed_dict: dict
    attempts: int
    revisions: list = field(default_factory=list)


def propose_seed(work, era_hint=None, max_attempts=3):
    """Analyze work → propose seed draft. Returns Proposal.

    Stub emits a deterministic proposal; C2's human-reviewed loop then
    validates via tools/muse_seed_cli, and fails feed back as constraints.
    """
    attempts = 0
    proposal_dict = _propose(work, era_hint)
    attempts += 1
    return Proposal(seed_dict=proposal_dict, attempts=attempts)


def _propose(work, era_hint):
    """Budget-driven seed proposal from W1 IR + W3 analysis signals.

    Tempo bounds come from muse_budgets (C3, measured corpus ranges);
    density/energy defaults stay stub-level per the design doc."""
    meta = getattr(work, "meta", None)
    era = era_hint or _getattr_meta(meta, "era", "classical")
    from muse_budgets import suggest
    era_budget = suggest(era)
    tempo_quick = (era_budget["tempo_bpm"]["min"] + era_budget["tempo_bpm"]["max"]) / 2
    n_parts = len(work.parts)
    n_notes = sum(len(p.notes) for p in work.parts)
    max_pitch = max(
        (n.pitch for p in work.parts for n in p.notes
         if n.pitch is not None),
        default=96,
    )
    min_pitch = min(
        (n.pitch for p in work.parts for n in p.notes
         if n.pitch is not None),
        default=36,
    )
    return {
        "format_version": "0.1",
        "work_id": _getattr_meta(meta, "work_id", "unknown"),
        "title": _getattr_meta(meta, "title", None) or "draft",
        "params": {
            "tempo": {
                "min_bpm": tempo_quick - 30,
                "max_bpm": tempo_quick + 30,
                "default_bpm": tempo_quick,
            },
            "energy": {"level": 0.5, "shape": "arch"},
            "density": {
                "min_notes_per_beat": 0.5,
                "max_notes_per_beat": float(n_notes) / max(1, n_parts) / 10,
            },
            "variation": {"level": 1, "points": []},
        },
        "philosophy": {
            "tempo_philosophy": ["flexible", "architectural"],
            "dynamic_philosophy": ["terraced", "dramatic"],
            "articulation_stance": ["consort"],
            "provenance": {
                "author": "muse_author",
                "ai_assisted": True,
            },
        },
        "variation_points": [],
        "assertions": {
            "register": {"part": work.parts[0].id if work.parts else "P1",
                          "min": _pitch_to_note(min_pitch),
                          "max": _pitch_to_note(max_pitch)},
            "tempo_bounds": {"min_bpm": tempo_quick - 40,
                              "max_bpm": tempo_quick + 40},
        },
        "provenance": {"source": _getattr_meta(meta, "source_format", ""),
                        "author": "muse_author", "era_hint": era},
        "era_budget": era_budget,
    }


def _getattr_meta(meta, key, default=None):
    if meta is None:
        return default
    if key == "source_format":
        return getattr(meta, "source_format", default)
    if key == "work_id":
        return getattr(meta, "title", None) or default
    if key == "era":
        return getattr(meta, "era", default)
    if key == "title":
        return getattr(meta, "title", default)
    return getattr(meta, key, default)


_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _pitch_to_note(pitch):
    return _NOTE_NAMES[pitch % 12] + str(pitch // 12 - 1)
