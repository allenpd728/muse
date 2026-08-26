"""Growth harness: one iteration + compare against the prior delta.

grow_one(seed) → (delta, stand_in_flag). compare_deltas(new, prior) →
GrowthReport with a verdict per trait (growing / flat / regressing).

The mockup path is the deterministic L1 stand-in (same stand-in the probe
engine uses) — a flat mockup means growth cannot be measured, which the
report marks explicitly. When the real L1 generate loop lands, MOCKUP_FN
swaps to it here, same contract as the probe engine's pin.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from muse_distill import seed_revision
from muse_mockup import Mockup, Note


def _mockup_from_work(work):
    """Deterministic L1 stand-in (same shape as the probe engine's stand-in):
    flat-velocity notes at score onsets with zero offsets."""
    mockup = Mockup(work_id=getattr(getattr(work, "meta", None), "title", None) or "unknown")
    mockup.ppq = getattr(getattr(work, "meta", None), "ppq", 480)  # the tick domain (#246)
    for p in work.parts:
        for n in p.notes:
            if n.pitch is None or "unpitched" in n.notations:
                continue
            mockup.notes.append(
                Note(
                    pitch=n.pitch,
                    onset=n.onset,
                    duration=n.duration,
                    velocity=64,
                    part=p.id,
                )
            )
    return mockup


MOCKUP_FN = _mockup_from_work  # real L1 generate loop swaps this when it lands


def grow_one(work, seed):
    """One iteration: build a mockup from the work via MOCKUP_FN, distill it,
    return (delta_dict, stand_in_flag)."""
    try:
        mockup = MOCKUP_FN(work)
    except Exception as e:
        return {"error": f"mockup generation failed: {e}"}, True
    try:
        delta = seed_revision(mockup)
    except Exception as e:
        return {"error": f"distill failed: {e}"}, True
    return delta, True


def _trait_delta(new_val, prior_val):
    """Numeric trait delta with a verdict."""
    try:
        diff = new_val - prior_val
    except TypeError:
        diff = None
    if diff is None or diff == 0:
        return {"verdict": "flat", "delta": 0}
    return {"verdict": "growing" if diff > 0 else "regressing", "delta": round(diff, 4)}


@dataclass
class GrowthReport:
    seed_id: str
    traits: dict = field(default_factory=dict)
    stand_in: bool = True

    def to_json(self) -> str:
        return json.dumps(
            {"seed_id": self.seed_id, "stand_in": self.stand_in,
             "traits": self.traits},
            sort_keys=True, indent=1,
        ) + "\n"


def compare_deltas(new_delta, prior_delta, seed_id, stand_in=True) -> GrowthReport:
    """Delta vs prior delta → per-trait growth report."""
    report = GrowthReport(seed_id=seed_id, stand_in=stand_in)

    numeric_traits = (
        ("velocity_pstdev", ("params", "dynamics", "velocity_pstdev")),
        ("rubato_pstdev_ms", ("params", "articulation", "rubato_pstdev_ms")),
        ("budget_position", ("params", "tempo", "default_bpm")),
        ("mockup_richness", ("provenance", None, "note_count")),
    )
    for name, (sec, sub, key) in numeric_traits:
        if sub is None:
            new_val = new_delta.get(sec, {}).get(key)
            old_val = prior_delta.get(sec, {}).get(key)
        else:
            new_val = new_delta["params"].get(sub, {}).get(key)
            old_val = prior_delta["params"].get(sub, {}).get(key)
        if isinstance(new_val, (int, float)) and isinstance(old_val, (int, float)):
            report.traits[name] = _trait_delta(new_val, old_val)
        else:
            report.traits[name] = {"verdict": "unknown", "delta": None}

    new_shape = new_delta.get("interpretation", {}).get("tempo_curve_shape")
    old_shape = prior_delta.get("interpretation", {}).get("tempo_curve_shape")
    report.traits["tempo_curve_shape"] = {
        "verdict": "same" if new_shape == old_shape else "changed",
        "from": old_shape,
        "to": new_shape,
    }
    return report
