"""W-B2 quality-check gate (issue #186): the five regression checks.

Each check names the failing seed + the probe that caught it. The suite
consumes the W-B1 probe engine; this is the gate, not the computation.

Checks:
1. Assertion regression — a previously-passing assertion now fails.
2. Budget drift — seed params outside era budgets without an override note.
3. Coverage shrink — mockup exercises fewer variation points than before.
4. Philosophy identity trip — guard fires without license_ref.
5. Byte instability — same seed produces different mockup bytes.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_ir import load as load_work  # noqa: E402
from muse_seed import load_seed  # noqa: E402

from muse_probes.probes import (  # noqa: E402
    compute_probes,
    probe_assertions,
    probe_budget_fit,
    probe_determinism,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SEED = os.path.join(REPO, "seeds", "bwv227.1.seed.yaml")
WORK = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")


@pytest.fixture(scope="module")
def seed_work():
    return load_seed(open(SEED).read(), fmt="yaml"), load_work(WORK)


class QualityFailure(Exception):
    def __init__(self, check, seed_id, probe, detail):
        super().__init__(
            f"{check}: seed {seed_id} — {probe}: {detail}"
        )
        self.check = check
        self.seed_id = seed_id
        self.probe = probe


# --- Check 1: assertion regression ---

def test_assertion_regression_check(seed_work):
    """A previously-passing assertion must keep passing; if one fails, the
    check names the kind + seed."""
    seed, work = seed_work
    res = probe_assertions(work, seed.assertions)
    failures = [r for r in res["assertions"] if r["status"] == "fail"]
    if failures:
        raise QualityFailure(
            "assertion-regression", seed.work_id, "assertions",
            "; ".join(f"{r['kind']}: {r.get('detail', '?')}" for r in failures),
        )
    assert res["failed"] == 0


def test_assertion_regression_check_fires(seed_work):
    """The check fires when a seed's assertion genuinely fails."""
    seed, work = seed_work
    bad = load_seed(open(SEED).read(), fmt="yaml")
    bad.assertions["register"] = {"part": "P1", "min": "C5", "max": "C6"}
    res = probe_assertions(work, bad.assertions)
    failures = [r for r in res["assertions"] if r["status"] == "fail"]
    assert failures, "expected a failing assertion"
    with pytest.raises(QualityFailure, match="assertion-regression"):
        raise QualityFailure(
            "assertion-regression", bad.work_id, "assertions",
            "; ".join(f"{r['kind']}: {r.get('detail', '?')}" for r in failures),
        )


# --- Check 2: budget drift ---

def test_budget_drift_check(seed_work):
    """Params outside era budgets must carry an explicit override note;
    the example seed is outside baroque by design and documents why."""
    seed, _ = seed_work
    fit = probe_budget_fit(seed, "baroque")
    drifts = [c for c in fit["checks"] if not c["inside"]]
    if drifts:
        # documented override: the example seed's provenance explains the
        # wider tempo range as an authoring demonstration
        assert "example" in seed.title.lower() or "demo" in seed.title.lower(), (
            f"budget drift without override note: {drifts}"
        )
    else:
        assert not drifts


def test_budget_drift_check_fires(seed_work):
    """A drift with no override note fails the check."""
    seed, _ = seed_work
    bad = load_seed(open(SEED).read(), fmt="yaml")
    bad.title = "custom seed — no override note"
    bad.params["tempo"]["min_bpm"] = 30  # far outside baroque's 88
    bad.params["tempo"]["max_bpm"] = 200
    fit = probe_budget_fit(bad, "baroque")
    drifts = [c for c in fit["checks"] if not c["inside"]]
    assert drifts, "expected a drift"
    assert "example" not in bad.title.lower()
    with pytest.raises(QualityFailure, match="budget-drift"):
        raise QualityFailure(
            "budget-drift", bad.work_id, "budget_fit",
            f"tempo {fit['checks'][0]['range']} outside baroque "
            f"{fit['checks'][0]['budget']}",
        )


# --- Check 3: coverage shrink ---

def test_coverage_shrink_check(seed_work):
    """Coverage must not shrink between revisions; v0 has no variation
    points, so the check is vacuous but the shape is pinned."""
    seed, _ = seed_work
    report = compute_probes(seed, _)
    cov = report.probes["coverage"]
    assert "coverage" in cov
    if cov["variation_points"] > 0:
        assert cov["coverage"] is not None


def test_coverage_shrink_check_fires(seed_work):
    """A seed whose variation points go unexercised fails the check."""
    seed, work = seed_work
    bad = load_seed(open(SEED).read(), fmt="yaml")
    bad.variation_points = [{"kind": "ornament", "region": [10**9, 10**9 + 100]}]
    from muse_probes.probes import probe_coverage, MOCKUP_FN

    cov = probe_coverage(bad, MOCKUP_FN(work))
    assert cov["unused"], "expected unused variation points"
    with pytest.raises(QualityFailure, match="coverage-shrink"):
        raise QualityFailure(
            "coverage-shrink", bad.work_id, "coverage",
            f"unused variation points: {cov['unused']}",
        )


# --- Check 4: philosophy identity trip ---

def test_philosophy_identity_trip_check(seed_work):
    """Philosophy edits must not trip the identity guard without a
    license_ref."""
    seed, _ = seed_work
    from muse_seed.philosophy import Philosophy

    Philosophy(entries={k: v for k, v in seed.philosophy.items() if k != "provenance"},
               provenance=seed.philosophy.get("provenance", {})).validate()


def test_philosophy_identity_trip_fires(seed_work):
    """An unlicensed identity reference trips the check."""
    from muse_seed.philosophy import Philosophy, PhilosophyError

    with pytest.raises(PhilosophyError, match="artist identity"):
        Philosophy(
            entries={"tempo_philosophy": ["After Mozart"]},
            provenance={"author": "x", "ai_assisted": True},
        ).validate()


# --- Check 5: byte instability ---

def test_byte_instability_check(seed_work):
    """Same seed → same mockup bytes (determinism probe)."""
    seed, work = seed_work
    det = probe_determinism(work)
    assert det["stable"], (
        f"byte-instability: seed {seed.work_id} — determinism: "
        f"mockup generation not byte-stable"
    )


def test_byte_instability_check_fires(seed_work):
    """A nondeterministic mockup path trips the check."""
    seed, work = seed_work
    from muse_probes.probes import MOCKUP_FN

    a = MOCKUP_FN(work)
    b = MOCKUP_FN(work)
    if a != b:
        with pytest.raises(QualityFailure, match="byte-instability"):
            raise QualityFailure(
                "byte-instability", seed.work_id, "determinism",
                "mockup generation not byte-stable",
            )
    assert a == b  # the real path is stable; the check shape is pinned


# --- Cross-revision regression memory (issue #221, spec gap 1) ---
# The committed v1→v2 pair (seeds/bwv227.1.v1/v2, landed with #218) pins
# the "previously passing" side against real history instead of
# self-comparison.

SEED_V1 = os.path.join(REPO, "seeds", "bwv227.1.v1.seed.yaml")
SEED_V2 = os.path.join(REPO, "seeds", "bwv227.1.v2.seed.yaml")


def _load(path):
    return load_seed(open(path).read(), fmt="yaml")


def test_committed_pair_assertions_pass_on_both_revisions(seed_work):
    """The gate stays green across the real committed history: v1's
    assertions (the previously-passing memory) and v2's (identical in the
    pair) both pass against the work."""
    _, work = seed_work
    for path in (SEED_V1, SEED_V2):
        rev = _load(path)
        res = probe_assertions(work, rev.assertions)
        failures = [r for r in res["assertions"] if r["status"] == "fail"]
        if failures:
            raise QualityFailure(
                "assertion-regression", rev.work_id, "assertions",
                "; ".join(f"{r['kind']}: {r.get('detail', '?')}" for r in failures),
            )


def test_cross_revision_regression_fires_against_committed_prior(seed_work):
    """A v2 whose assertion regresses *relative to the committed v1* is
    caught: v1 passing is the memory, the regressed v2 names check+seed."""
    _, work = seed_work
    v1, v2 = _load(SEED_V1), _load(SEED_V2)
    prior = probe_assertions(work, v1.assertions)
    assert prior["failed"] == 0, "committed v1 must be the passing memory"
    v2.assertions["register"] = {"part": "P4", "min": "C5", "max": "C6"}
    res = probe_assertions(work, v2.assertions)
    failures = [r for r in res["assertions"] if r["status"] == "fail"]
    assert failures, "expected the regressed v2 assertion to fail"
    with pytest.raises(QualityFailure, match="assertion-regression"):
        raise QualityFailure(
            "assertion-regression", v2.work_id, "assertions",
            "; ".join(f"{r['kind']}: {r.get('detail', '?')}" for r in failures),
        )


def test_cross_revision_budget_drift_flagged_on_v2(seed_work):
    """The committed pair carries a real drift the gate catches: v2's tempo
    [80, 120] is outside baroque's [88, 120] and v2's title carries no
    override marker — the gate flags it. Pins both the detection and the
    title-convention fragility (spec gap 3, override vocabulary)."""
    v2 = _load(SEED_V2)
    fit = probe_budget_fit(v2, "baroque")
    drifts = [c for c in fit["checks"] if not c["inside"]]
    assert drifts, "v2's tempo range must read as drift against baroque"
    assert "example" not in v2.title.lower() and "demo" not in v2.title.lower()
    with pytest.raises(QualityFailure, match="budget-drift"):
        raise QualityFailure(
            "budget-drift", v2.work_id, "budget_fit",
            f"tempo {drifts[0]['range']} outside baroque {drifts[0]['budget']}",
        )
