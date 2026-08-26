"""Probe engine tests (issue #185).

Determinism guarantee, seven probe contracts, CLI gate, and the
workbench-rendering shape (stable keys, JSON-serializable).
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_ir import load as load_work  # noqa: E402
from muse_seed import load_seed  # noqa: E402

from muse_probes.probes import (  # noqa: E402
    MOCKUP_FN,
    ProbeError,
    compute_probes,
    probe_assertions,
    probe_budget_fit,
    probe_coverage,
    probe_determinism,
    probe_delta_curves,
    probe_fidelity_guard,
    probe_param_diff,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SEED = os.path.join(REPO, "seeds", "bwv227.1.seed.yaml")
SEED_V1 = os.path.join(REPO, "seeds", "bwv227.1.v1.seed.yaml")
SEED_V2 = os.path.join(REPO, "seeds", "bwv227.1.v2.seed.yaml")
SEED_VARIATION = os.path.join(
    REPO, "tools", "muse_probes", "tests", "fixtures",
    "bwv227.1.variation.seed.yaml")
WORK = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")
CLI = os.path.join(REPO, "tools", "muse_probes", "cli.py")


@pytest.fixture(scope="module")
def seed_work():
    return load_seed(open(SEED).read(), fmt="yaml"), load_work(WORK)


PROBE_KEYS = (
    "param_diff",
    "budget_fit",
    "assertions",
    "coverage",
    "delta_curves",
    "determinism",
    "fidelity_guard",
    "lineage",  # W-B9 (#253) — eighth probe per seed-workbench.md probe table
)


def test_all_probes_present(seed_work):
    seed, work = seed_work
    report = compute_probes(seed, work)
    for key in PROBE_KEYS:
        assert key in report.probes, f"{key} missing"


def test_deterministic_report(seed_work):
    seed, work = seed_work
    a = compute_probes(seed, work)
    b = compute_probes(seed, work)
    assert a.to_json() == b.to_json()


def test_fidelity_guard_on_clean_mockup(seed_work):
    seed, work = seed_work
    mockup = [(p.id, n.pitch, n.onset, n.duration)
              for p in work.parts for n in p.notes
              if n.pitch is not None and "unpitched" not in n.notations]
    guard = probe_fidelity_guard(work, mockup)
    assert guard["fidelity"], guard


def test_fidelity_guard_catches_missing_notes(seed_work):
    seed, work = seed_work
    mockup = [(p.id, n.pitch, n.onset, n.duration)
              for p in work.parts for n in p.notes[1:]
              if n.pitch is not None and "unpitched" not in n.notations]
    guard = probe_fidelity_guard(work, mockup)
    assert not guard["fidelity"]
    assert guard["missing"] >= 1


def test_param_diff_detects_change(seed_work):
    seed, _ = seed_work
    prior = load_seed(open(SEED).read(), fmt="yaml")
    prior.params["tempo"]["min_bpm"] = 60
    diff = probe_param_diff(seed, prior)
    assert diff["status"] == "compared"
    assert "params" in diff["changes"]


def test_budget_fit_marks_range_position(seed_work):
    seed, _ = seed_work
    fit = probe_budget_fit(seed, "baroque")
    tempo = next(c for c in fit["checks"] if c["param"] == "tempo")
    assert "range" in tempo and "inside" in tempo
    assert fit["provisional"] is False


def test_assertions_report_per_kind(seed_work):
    seed, work = seed_work
    res = probe_assertions(work, seed.assertions)
    kinds = {r["kind"] for r in res["assertions"]}
    assert {"register", "tempo_bounds"} <= kinds


def test_gate_ok_flag_toggles(seed_work):
    """The gate flips when a gate probe fails — via a seed with a failing
    assertion (register bound that excludes the actual range)."""
    seed, work = seed_work
    report = compute_probes(seed, work)
    assert report.ok is True
    bad_seed = load_seed(open(SEED).read(), fmt="yaml")
    bad_seed.assertions["register"] = {"part": "P1", "min": "C5", "max": "C6"}
    bad = compute_probes(bad_seed, work)
    assert bad.ok is False
    assert bad.probes["assertions"]["failed"] == 1


def test_json_is_stable_shape(seed_work):
    seed, work = seed_work
    report = compute_probes(seed, work)
    parsed = json.loads(report.to_json())
    assert parsed["seed_id"] == "bwv227.1"
    assert set(parsed["probes"]) == set(PROBE_KEYS)


def test_cli_gate_and_output(tmp_path):
    proc = subprocess.run(
        [sys.executable, CLI, os.path.relpath(SEED, REPO), "--era", "baroque"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr[:300]
    parsed = json.loads(proc.stdout)
    assert parsed["ok"] is True
    out = tmp_path / "probe.json"
    proc2 = subprocess.run(
        [sys.executable, CLI, os.path.relpath(SEED, REPO), "--out", str(out)],
        capture_output=True, text=True,
    )
    assert proc2.returncode == 0
    assert json.loads(out.read_text())["ok"] is True


class TestPriorRevisionWiring:
    """Follow-up from tests/open_20260824-001000_wb1-probe-engine.md: pin the
    param_diff shape against the committed two-revision pair (G3 fixtures,
    seeds/bwv227.1.v1 → v2) — the shape workbench history rows consume."""

    def test_revision_pair_diff_shape(self, seed_work):
        _, work = seed_work
        v1 = load_seed(open(SEED_V1).read(), fmt="yaml")
        v2 = load_seed(open(SEED_V2).read(), fmt="yaml")
        diff = probe_param_diff(v2, prior_seed=v1)
        assert diff["status"] == "compared"
        # Only params differ between the committed revisions; title is not a
        # compared section.
        assert set(diff["changes"]) == {"params"}
        change = diff["changes"]["params"]
        assert change["from"]["tempo"]["min_bpm"] == 62
        assert change["to"]["tempo"]["min_bpm"] == 80
        assert change["from"]["tempo"]["max_bpm"] == 129
        assert change["to"]["tempo"]["max_bpm"] == 120
        assert change["from"]["energy"]["level"] == 0.5
        assert change["to"]["energy"]["level"] == 0.75
        assert change["from"]["density"]["max_notes_per_beat"] == 4
        assert change["to"]["density"]["max_notes_per_beat"] == 6

    def test_report_wires_prior_seed(self, seed_work):
        _, work = seed_work
        v1 = load_seed(open(SEED_V1).read(), fmt="yaml")
        v2 = load_seed(open(SEED_V2).read(), fmt="yaml")
        report = compute_probes(v2, work, prior_seed=v1)
        assert report.probes["param_diff"]["status"] == "compared"
        parsed = json.loads(report.to_json())
        assert parsed["probes"]["param_diff"]["changes"]["params"]["to"][
            "tempo"]["min_bpm"] == 80

    def test_no_prior_shape(self, seed_work):
        seed, work = seed_work
        report = compute_probes(seed, work)
        assert report.probes["param_diff"] == {"status": "no-prior",
                                               "changes": {}}


class TestCoverageWithRealVariationPoints:
    """Follow-up: a seed with actual regions pins exercised/unused — the
    example seed ships variation_points: []."""

    def test_exercised_and_unused_regions(self, seed_work):
        _, work = seed_work
        seed = load_seed(open(SEED_VARIATION).read(), fmt="yaml")
        report = compute_probes(seed, work)
        cov = report.probes["coverage"]
        assert cov == {"variation_points": 2, "exercised": 1,
                       "unused": ["tempo_flex"], "coverage": 0.5}

    def test_gate_still_ok_with_variation_points(self, seed_work):
        _, work = seed_work
        seed = load_seed(open(SEED_VARIATION).read(), fmt="yaml")
        report = compute_probes(seed, work)
        assert report.ok is True


def test_mockup_fn_contract(seed_work):
    """The pin the real L1 swap must satisfy unchanged: MOCKUP_FN takes the
    work and returns deterministic (part, pitch, onset, duration) tuples."""
    _, work = seed_work
    a = MOCKUP_FN(work)
    b = MOCKUP_FN(work)
    assert a == b and a, "MOCKUP_FN must be deterministic and non-empty"
    for part, pitch, onset, duration in a:
        assert isinstance(part, str)
        assert pitch is not None
        assert isinstance(onset, int)
        assert duration > 0


# --- W-B9 lineage probe (issue #261; spec
# tests/open_20260826-003500_wb9-lineage-probe.md) ---

from muse_probes.probes import probe_lineage  # noqa: E402


def _write_seed(tmp_path, name, extends=None):
    """Minimal valid seed file, optionally with a lineage pointer."""
    import hashlib
    text = (
        "format_version: '0.1'\n"
        "work_id: bwv227.1\n"
        "params: {tempo: {min_bpm: 60, max_bpm: 120}}\n"
        "assertions: {tempo_bounds: {min_bpm: 60, max_bpm: 120}}\n"
        f"provenance: {{author: t, ai_assisted: false{', extends: ' + extends if extends else ''}}}\n"
    )
    p = tmp_path / name
    p.write_text(text)
    return str(p), hashlib.sha256(text.encode()).hexdigest()


def test_lineage_root_is_root_not_verified(tmp_path):
    """Regression pin: a bare seed (no extends) reports 'root' — never
    'verified' (nothing was verified)."""
    path, _ = _write_seed(tmp_path, "a.seed.yaml")
    res = probe_lineage(path, store_dirs=[str(tmp_path)])
    assert res["status"] == "root"
    assert res["hops"][-1]["status"] == "root"


def test_lineage_verified_chain(tmp_path):
    """parent ← child: both hops resolve, child verifies."""
    parent_path, parent_hash = _write_seed(tmp_path, "parent.seed.yaml")
    child_path, _ = _write_seed(tmp_path, "child.seed.yaml", extends=parent_hash)
    res = probe_lineage(child_path, store_dirs=[str(tmp_path)])
    assert res["status"] == "verified"
    assert [h["status"] for h in res["hops"]] == ["verified", "root"]


def test_lineage_missing_pointer(tmp_path):
    path, _ = _write_seed(tmp_path, "orphan.seed.yaml", extends="f" * 64)
    res = probe_lineage(path, store_dirs=[str(tmp_path)])
    assert res["status"] == "missing"
    assert res["hops"][0]["status"] == "missing"


def test_lineage_unknown_without_seed_path():
    res = probe_lineage(None)
    assert res["status"] == "unknown"
    assert res["hops"] == []
    assert "no seed path" in res["note"]


def test_lineage_orthogonal_to_gate(seed_work, tmp_path):
    """Gate orthogonality pin: a seed whose lineage is 'missing' but whose
    fidelity/determinism/assertions pass still yields ok=True — integrity
    is a separate signal, not part of the gate."""
    seed, work = seed_work
    path, _ = _write_seed(tmp_path, "orphan.seed.yaml", extends="f" * 64)
    orphan = load_seed(open(path).read(), fmt="yaml")
    # give the orphan the reference seed's passing assertions so the gate
    # inputs are all green except lineage
    orphan.assertions = seed.assertions
    report = compute_probes(orphan, work, seed_path=path)
    assert report.probes["lineage"]["status"] == "missing"
    assert report.ok is True


def test_cli_writes_lineage_block(tmp_path):
    out = tmp_path / "probes.json"
    r = subprocess.run(
        [sys.executable, CLI, SEED_V2, "--work", WORK, "--out", str(out)],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    probes = json.loads(out.read_text())["probes"]
    assert probes["lineage"]["status"] in ("root", "verified", "missing", "broken")


def test_explorer_workbench_carries_lineage(tmp_path):
    """Explorer seam: generate_workbench output carries a lineage block per
    seed; the committed bwv227.1 chain's statuses are pinned."""
    from muse_explorer.generate import generate_workbench
    out = generate_workbench(str(tmp_path))
    seeds_dir = os.path.join(str(tmp_path), "data", "seeds")
    files = [f for f in os.listdir(seeds_dir) if f.endswith(".probes.json")]
    assert files, "no probe artifacts generated"
    statuses = []
    for f in sorted(files):
        probes = json.loads(open(os.path.join(seeds_dir, f)).read())["probes"]
        assert "lineage" in probes, f"{f} missing lineage block"
        statuses.append(probes["lineage"]["status"])
    # the committed chain: v1 root → v2 verified; base seed root
    assert set(statuses) <= {"root", "verified"}, statuses
    assert "verified" in statuses and "root" in statuses
