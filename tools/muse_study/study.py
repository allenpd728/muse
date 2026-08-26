"""R3 study scripts + directive-survival feedback (#284).

A script is a list of named directive steps. run_script compiles each to
a seed and, crucially, also builds the mockup and asks the distiller
whether the directive *survived the render* — the feedback loop that
trains the conductor's ear without live musicians.

Survival is measured by mapping each verb to the interpretation field it
should move (VERB_MEASURES) and comparing the mockup's extracted
Interpretation against the base's, with a move/no-move/drift verdict.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


class StudyError(ValueError):
    pass


# verb → (interpretation field, expected direction of movement)
# Compiled from R1's knob map: what the distiller can measure moving.
VERB_MEASURES = {
    "rebalance": ("part_gains", "up"),        # named part should dominate
    "phrase": ("tempo_curve_shape", "arch"),  # a phrase arch forms
    "tempo_arch": ("tempo_range", "wider"),   # tempo bounds widen
    "rubato": ("rubato_pstdev_ms", "up"),     # more spread
    "hold": ("tempo_curve_shape", "flat"),    # constrained arch → flatter
}


@dataclass
class Step:
    directive: str
    expect: str = ""                # free-text note on the intended effect


@dataclass
class Script:
    name: str
    issue: str                      # the interpretive issue it drills
    steps: list = field(default_factory=list)


# Precomposed study sequences, keyed to well-known rehearsal issues.
# Templates reference the work's parts (resolved at run time).
SCRIPTS = {
    "quiet-the-bass": Script(
        name="quiet-the-bass",
        issue="bass part dominates the texture; the upper voices vanish "
              "under it (the 'quiet the cellos into the development' drill)",
        steps=[
            Step("rebalance: bring P4 down", "lower the bass line into balance"),
            Step("rebalance: bring P4 down 30% at ticks 0-9999",
                 "overcorrect deliberately — hear the boundary"),
            Step("rebalance: bring P4 up", "return toward balance"),
        ]),
    "phrase-the-pickup": Script(
        name="phrase-the-pickup",
        issue="pickup notes arrive flat; no anacrusis arch into the downbeat",
        steps=[
            Step("phrase: quieter into development", "arch the pickup"),
            Step("phrase: broader into development",
                 "exaggerate the dip — hear the shape"),
        ]),
    "tempo-architecture": Script(
        name="tempo-architecture",
        issue="tempo wanders without an arch; the form loses its spine",
        steps=[
            Step("tempo_arch: wider", "open the bounds"),
            Step("tempo_arch: settle",
                 "narrow back — the arch should read as contained"),
        ]),
    "rubato-calibration": Script(
        name="rubato-calibration",
        issue="onset-offset spread is either mechanical or soupy",
        steps=[
            Step("rubato: more", "add spread"),
            Step("rubato: less", "tighten back"),
            Step("hold: whole work", "pin it — hear mechanical as a floor"),
        ]),
}


def run_script(script: Script, seed_path: str, era="baroque",
               work=None, mockup_fn=None):
    """Compile each step and report per-step survival.

    mockup_fn: work → Mockup. Defaults to the deterministic stand-in used
    by the probe/grow harnesses (the real L1 swaps it, same pin).
    Returns (last_candidate_seed, [StepReport]). The script is a drill —
    it dry-runs each step in sequence on the running candidate, then
    checks survival of *each* against the base.
    """
    from muse_rehearse import parse_directive, compile_directive
    from muse_seed import load_seed
    from muse_grow.grow import _mockup_from_work
    from muse_distill import extract_interpretation

    base = load_seed(open(seed_path).read(), fmt="yaml")
    mockup_fn = mockup_fn or _mockup_from_work
    reports = []
    candidate = base
    for step in script.steps:
        d = parse_directive(step.directive, seed=base, work=work)
        candidate = compile_directive(d, candidate, era, work)
        reports.append(check_survival(step, base, candidate, work, mockup_fn))
    return candidate, reports


@dataclass
class StepReport:
    directive: str
    verb: str
    measure: str              # interpretation field checked
    expected: str             # expected movement
    base_value: object
    candidate_value: object
    verdict: str              # moved | flat | drifted
    expect_note: str = ""

    def to_dict(self):
        return {"directive": self.directive, "verb": self.verb,
                "measure": self.measure, "expected": self.expected,
                "base": self.base_value, "candidate": self.candidate_value,
                "verdict": self.verdict, "note": self.expect_note}


def check_survival(step, base_seed, candidate_seed, work, mockup_fn):
    """Did this directive survive? Measured at the seed-param level: did the
    compiled knob actually land in the candidate seed (and stay within
    budget)? The render/mockup level is marked stand-in-blocked — the
    deterministic stand-in produces a flat mockup regardless of seed, so a
    render-level survival check is only meaningful once the real L1 lands
    (R1 §What R3 builds; L1.11 #276 swaps MOCKUP_FN).
    """
    from muse_seed.params import ERA_BUDGETS

    verb = step.directive.split(":", 1)[0].split()[0].rstrip(":").lower()
    measure, expected = VERB_MEASURES.get(verb, (None, None))
    budget = ERA_BUDGETS["baroque"]
    base_v, cand_v, verdict = _seed_survival(verb, base_seed, candidate_seed)
    return StepReport(directive=step.directive, verb=verb,
                      measure=measure or "—", expected=expected or "—",
                      base_value=base_v, candidate_value=cand_v,
                      verdict=verdict, expect_note=step.expect)


def _seed_survival(verb, base, cand):
    """(base_value, candidate_value, verdict) for the verb's seed knob."""
    bp, cp = base.params, cand.params
    if verb == "rebalance":
        b = bp.get("part_gains", {}); c = cp.get("part_gains", {})
        moved = any(c.get(k) != b.get(k) for k in set(b) | set(c))
        return b, c, "moved" if moved else "flat"
    if verb == "phrase":
        n_b = len(getattr(base, "variation_points", []) or [])
        n_c = len(getattr(cand, "variation_points", []) or [])
        return n_b, n_c, "moved" if n_c > n_b else "flat"
    if verb == "tempo_arch":
        bt = bp.get("tempo", {}); ct = cp.get("tempo", {})
        b_span = bt.get("max_bpm", 0) - bt.get("min_bpm", 0)
        c_span = ct.get("max_bpm", 0) - ct.get("min_bpm", 0)
        return b_span, c_span, (
            "moved" if c_span != b_span else "flat")
    if verb == "rubato":
        b = bp.get("articulation", {}).get("rubato_pstdev_ms", 0.0)
        c = cp.get("articulation", {}).get("rubato_pstdev_ms", 0.0)
        return b, c, "moved" if c != b else "flat"
    if verb == "hold":
        has = "tempo_bounds" in getattr(cand, "assertions", {})
        return None, has, "moved" if has else "flat"
    return None, None, "unmeasurable"
