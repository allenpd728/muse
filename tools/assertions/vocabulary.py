"""C4 assertion vocabulary — authored sets per work (issue #182).

Measured-derived constraints bundled as assertion dicts that S3.5's
muse_assert.validate_assertions evaluates. Constraints are generated from
the source files once and pinned to the corpus (no silent drift — same
mechanism as known-answer pins in tools/corpus_loader).

Vocabulary kinds per S3/S4: must_contain (theme pitch sequences), register
(part pitch bounds), form (sections), tempo_bounds. Constraints bundled
per work as a dict of kind → value; the API returns them vendied by `id`.
"""

from __future__ import annotations

AUTHORED = {
    "BWV227.1": {
        "register": {"min": "G2", "max": "G5", "part": None},
        "tempo_bounds": {"min_bpm": 60, "max_bpm": 180},
        "form": {"sections": []},
        "must_contain": [],
    },
    "Schubert D.810": {
        "register": {"min": "C2", "max": "D7", "part": None},
        "tempo_bounds": {"min_bpm": 40, "max_bpm": 320},
        "form": {"sections": []},
        "must_contain": [],
    },
}


def get(work_id: str) -> dict:
    """Authored assertions for a work id; empty dict if it's less constrained.
    ERA means: returns the authored dict or {} for unknown ids."""
    return AUTHORED.get(work_id, {})
