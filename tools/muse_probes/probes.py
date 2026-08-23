"""Probe computation: seed + work → deterministic probe report.

Seven probes per docs/design/seed-workbench.md:

1. param_diff        — seed params vs a prior revision (when supplied)
2. budget_fit        — seed ranges vs era budgets (C3); center/edge position
3. assertions        — seed assertions evaluated against the work (S3.5)
4. coverage          — mockup realization of sanctioned variation points
5. delta_curves      — mockup IOI shape vs source vs era norm
6. determinism       — same generation path twice → identical artifact
7. fidelity_guard    — mockup never contradicts the score (W4, tolerance 0)

The mockup path here is the deterministic L1 stand-in (work → flat-velocity
notes, same as tools/muse_mockup/cli.py): it exists so the probes run
today. When the real L1 generate loop lands, MOCKUP_FN swaps to it — same
contract as the P1 DECODER pin.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


class ProbeError(ValueError):
    """A probe could not be computed (missing input, unsupported shape)."""


@dataclass
class ProbeReport:
    seed_id: str
    work_id: str
    probes: dict = field(default_factory=dict)
    ok: bool = True

    def to_json(self) -> str:
        return json.dumps(
            {"seed_id": self.seed_id, "work_id": self.work_id,
             "ok": self.ok, "probes": self.probes},
            sort_keys=True, indent=1,
        ) + "\n"


def _mockup_from_work(work):
    """Deterministic L1 stand-in: work → flat-velocity note list."""
    notes = []
    for p in work.parts:
        for n in p.notes:
            if n.pitch is None or "unpitched" in n.notations:
                continue
            notes.append((p.id, n.pitch, n.onset, n.duration))
    return notes


MOCKUP_FN = _mockup_from_work  # real L1 generate loop swaps this when it lands


def _ioi_curve(notes_by_part):
    """Inter-onset intervals per part, in order."""
    curves = {}
    for part, seq in notes_by_part.items():
        onsets = sorted(o for _, _, o, _ in seq) if seq and len(seq[0]) == 4 else sorted(seq)
        curves[part] = [b - a for a, b in zip(onsets, onsets[1:])]
    return curves


def probe_param_diff(seed, prior_seed=None):
    """Probe 1: what changed between this seed and the prior revision."""
    if prior_seed is None:
        return {"status": "no-prior", "changes": {}}
    changes = {}
    for section in ("params", "philosophy", "variation_points", "assertions"):
        a, b = getattr(seed, section, None), getattr(prior_seed, section, None)
        if a != b:
            changes[section] = {"from": b, "to": a}
    return {"status": "compared", "changes": changes}


def probe_budget_fit(seed, era="baroque"):
    """Probe 2: seed tempo/dynamics ranges vs era budgets (C3)."""
    from muse_budgets import budgets as era_budgets

    budget = era_budgets(era)
    tempo = getattr(seed, "params", {}).get("tempo", {})
    out = {"era": era, "provisional": budget.provisional, "checks": []}
    lo, hi = tempo.get("min_bpm"), tempo.get("max_bpm")
    default = tempo.get("default_bpm")
    if lo is not None and hi is not None:
        inside = budget.tempo_bpm_min <= lo and hi <= budget.tempo_bpm_max
        span = hi - lo
        allowed = budget.tempo_bpm_max - budget.tempo_bpm_min
        position = "center"
        if default is not None:
            center = (budget.tempo_bpm_min + budget.tempo_bpm_max) / 2
            edge = allowed * 0.2
            if abs(default - center) > allowed / 2 - edge:
                position = "edge"
        out["checks"].append({
            "param": "tempo",
            "range": [lo, hi],
            "budget": [budget.tempo_bpm_min, budget.tempo_bpm_max],
            "inside": inside,
            "span_fraction": round(span / allowed, 3) if allowed else None,
            "default_position": position,
        })
    return out


def probe_assertions(work, assertions):
    """Probe 3: an assertions dict evaluated against the work (S3.5).

    Takes the assertions mapping directly (not the seed) so both
    compute_probes and the quality gate share one signature.
    """
    from muse_assert import AssertionError, validate_assertions

    results = []
    assertions = assertions or {}
    for kind, rule in assertions.items():
        try:
            validate_assertions(work, {kind: rule})
            results.append({"kind": kind, "status": "pass"})
        except AssertionError as e:
            results.append({"kind": kind, "status": "fail", "detail": str(e)})
        except Exception as e:
            results.append({"kind": kind, "status": "error",
                            "detail": f"{type(e).__name__}: {e}"})
    return {"assertions": results,
            "passed": sum(1 for r in results if r["status"] == "pass"),
            "failed": sum(1 for r in results if r["status"] == "fail")}


def probe_coverage(seed, mockup_notes):
    """Probe 4: which sanctioned variation points the mockup exercises."""
    variation_points = getattr(seed, "variation_points", []) or []
    exercised = 0
    unused = []
    for vp in variation_points:
        region = vp.get("region", [0, 0]) if isinstance(vp, dict) else [0, 0]
        start, end = region
        hits = [n for n in mockup_notes if start <= n[2] < end]
        if hits:
            exercised += 1
        else:
            unused.append(vp.get("kind", "?") if isinstance(vp, dict) else "?")
    total = len(variation_points)
    return {"variation_points": total, "exercised": exercised,
            "unused": unused,
            "coverage": round(exercised / total, 3) if total else None}


def probe_delta_curves(work, mockup_notes):
    """Probe 5: mockup IOI shape vs source (delta-analysis vocabulary)."""
    src = {}
    for p in work.parts:
        src[p.id] = sorted(n.onset for n in p.notes if n.pitch is not None)
    mock = {}
    for part, pitch, onset, dur in mockup_notes:
        mock.setdefault(part, []).append(onset)
    stats = {}
    for part in src:
        a = [b - x for x, b in zip(src[part], src[part][1:])]
        b = [y - x for x, y in zip(sorted(mock.get(part, [])), sorted(mock.get(part, []))[1:])]
        if a and b:
            stats[part] = {
                "source_ioi_mean": round(sum(a) / len(a), 3),
                "mockup_ioi_mean": round(sum(b) / len(b), 3),
                "drift_ratio": round((sum(b) / len(b)) / (sum(a) / len(a)), 4)
                if sum(a) else None,
            }
    return {"parts": stats, "note": "mockup is the deterministic stand-in; "
            "LLM-shaped curves arrive with the real L1"}


def probe_determinism(work):
    """Probe 6: same generation path twice → identical artifact."""
    a = MOCKUP_FN(work)
    b = MOCKUP_FN(work)
    return {"stable": a == b, "notes": len(a)}


def probe_fidelity_guard(work, mockup_notes):
    """Probe 7: every score note present at the right onset (tolerance 0).

    Accepts (work, mockup) — the seed argument is unused, kept for call-site
    symmetry with other probes.
    """
    missing = extra = 0
    src = {(p.id, n.pitch, n.onset)
           for p in work.parts for n in p.notes
           if n.pitch is not None and "unpitched" not in n.notations}
    mock = {(part, pitch, onset) for part, pitch, onset, _ in mockup_notes}
    missing = len(src - mock)
    extra = len(mock - src)
    return {"score_notes": len(src), "mockup_notes": len(mock),
            "missing": missing, "extra": extra,
            "fidelity": missing == 0 and extra == 0}


def compute_probes(seed, work, prior_seed=None, era="baroque") -> ProbeReport:
    """Compute the full probe set. Deterministic for fixed inputs."""
    mockup = MOCKUP_FN(work)
    report = ProbeReport(
        seed_id=getattr(seed, "work_id", "unknown"),
        work_id=getattr(seed, "work_id", "unknown"),
    )
    report.probes = {
        "param_diff": probe_param_diff(seed, prior_seed),
        "budget_fit": probe_budget_fit(seed, era),
        "assertions": probe_assertions(work, getattr(seed, "assertions", {})),
        "coverage": probe_coverage(seed, mockup),
        "delta_curves": probe_delta_curves(work, mockup),
        "determinism": probe_determinism(work),
        "fidelity_guard": probe_fidelity_guard(work, mockup),
    }
    report.ok = (
        report.probes["fidelity_guard"]["fidelity"]
        and report.probes["determinism"]["stable"]
        and report.probes["assertions"]["failed"] == 0
    )
    return report
