"""muse_distill — L4 distiller (issue #196).

Mockup → extracted interpretation → seed revision (human-reviewable).
The learning loop: the prompt accumulates interpretive craft; later mockups
are cheaper and better.

Extraction: tempo curve shape, velocity distribution, onset-offset
distribution (rubato estimate), per-part balance, articulation frequency.
No auto-apply — output is a delta a human reviews and applies.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field

from muse_mockup import Mockup


@dataclass
class Interpretation:
    tempo_curve_shape: str       # "arch" | "flat" | "wavering"
    tempo_range: tuple           # (min_bpm, max_bpm)
    velocity_mean: float
    velocity_pstdev: float
    rubato_mean_ms: float
    rubato_pstdev_ms: float
    part_gains: dict = field(default_factory=dict)
    note_count: int = 0


def extract_interpretation(mockup: Mockup) -> Interpretation:
    """Mockup → measurable interpretation traits."""
    mockup.validate()
    bpms = [mbpm / 1000.0 for _, mbpm in mockup.tempo_map] or [120.0]
    if max(bpms) - min(bpms) < 2:
        shape = "flat"
    elif len(bpms) >= 3 and bpms[0] < bpms[-1] and bpms[1] > bpms[0]:
        shape = "arch"
    else:
        shape = "wavering"
    velocities = [n.velocity for n in mockup.notes]
    rubato = [n.onset_offset_ms for n in mockup.notes]
    part_gains = {}
    for p in mockup.notes:
        part_gains.setdefault(p.part, 0)
        part_gains[p.part] += 1
    return Interpretation(
        tempo_curve_shape=shape,
        tempo_range=(min(bpms), max(bpms)),
        velocity_mean=round(statistics.fmean(velocities), 2) if velocities else 0.0,
        velocity_pstdev=round(statistics.pstdev(velocities), 2) if len(velocities) > 1 else 0.0,
        rubato_mean_ms=round(statistics.fmean(rubato), 2) if rubato else 0.0,
        rubato_pstdev_ms=round(statistics.pstdev(rubato), 2) if len(rubato) > 1 else 0.0,
        part_gains=part_gains,
        note_count=len(mockup.notes),
    )


def seed_revision(mockup: Mockup, mockup_path: str = None) -> dict:
    """Mockup → seed revision dict a human can review and apply.

    S3.8b (#254): `operation` is always stamped (muse_distill produced
    this revision); when `mockup_path` is given (the persisted producing
    mockup), `extends` carries the SHA-256 of its committed bytes — the
    S3.7 lineage pointer.
    """
    i = extract_interpretation(mockup)
    return {
        "work_id": mockup.work_id,
        "params": {
            "tempo": {
                "default_bpm": round((i.tempo_range[0] + i.tempo_range[1]) / 2, 1),
                "min_bpm": i.tempo_range[0],
                "max_bpm": i.tempo_range[1],
            },
            "dynamics": {
                "mean_velocity": i.velocity_mean,
                "velocity_pstdev": i.velocity_pstdev,
            },
            "articulation": {
                "rubato_mean_ms": i.rubato_mean_ms,
                "rubato_pstdev_ms": i.rubato_pstdev_ms,
            },
        },
        "interpretation": {
            "tempo_curve_shape": i.tempo_curve_shape,
            "part_gains": i.part_gains,
        },
        "provenance": _provenance(mockup, i, mockup_path),
    }


def _provenance(mockup, interpretation, mockup_path):
    prov = {"distilled_from": mockup.work_id,
            "note_count": interpretation.note_count,
            "operation": "muse_distill@1"}
    if mockup_path:
        from muse_lineage.lineage import sha256_file
        prov["extends"] = sha256_file(mockup_path)
    return prov


def dump_delta(delta: dict, fmt="yaml") -> str:
    if fmt == "json":
        return json.dumps(delta, indent=2, sort_keys=True)
    import yaml
    return yaml.safe_dump(delta, sort_keys=False, allow_unicode=True)
