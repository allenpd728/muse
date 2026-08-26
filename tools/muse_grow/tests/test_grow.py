"""Growth harness tests (issue #203).

The report's trait verdicts are computed correctly; the stand-in is
marked; the CLI emits delta + report deterministically.
"""

import json
import os
import subprocess
import sys
import hashlib

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_ir import load  # noqa: E402

from muse_grow.grow import GrowthReport, compare_deltas, grow_one, _mockup_from_work  # noqa: E402


REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WORK = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")
CLI = os.path.join(REPO, "tools", "muse_grow", "cli.py")


@pytest.fixture(scope="module")
def work():
    return load(WORK)


TRAITS = (
    "velocity_pstdev",
    "rubato_pstdev_ms",
    "tempo_curve_shape",
    "budget_position",
    "mockup_richness",
)


def test_grow_one_returns_delta_and_stand_in(work):
    delta, stand_in = grow_one(work, None)
    assert stand_in is True
    assert "error" not in delta
    assert "params" in delta and "interpretation" in delta and "provenance" in delta


def test_compare_reports_all_traits(work):
    delta, _ = grow_one(work, None)
    prior = {"params": {"dynamics": {"velocity_pstdev": 0.0}},
             "articulation": {"rubato_pstdev_ms": 0.0},
             "tempo": {"default_bpm": 60.0},
             "interpretation": {"tempo_curve_shape": "flat"},
             "provenance": {"note_count": 0}}
    report = compare_deltas(delta, prior, "x")
    for trait in TRAITS:
        assert trait in report.traits


def test_grow_one_logs_expansion_entry(work):
    """G4 (#252): the delta carries wall-clock expansion time keyed by
    operation, with variation-point and note counts."""
    delta, _ = grow_one(work, None)
    exp = delta["expansion"]
    assert exp["expansion_time_ms"] >= 0
    assert exp["operation"] == "muse_grow@1"  # default when no seed
    assert exp["variation_point_count"] == 0
    assert exp["note_count"] == 279  # bwv227.1 pitched notes (W2 pin)


def test_expansion_entry_uses_seed_operation_tag(work):
    """A seed carrying provenance.operation (S3.7) keys the entry by it."""
    from muse_seed import Seed
    seed = Seed(format_version="0.1", work_id="bwv227.1",
                params={"tempo": {"min_bpm": 60, "max_bpm": 120}},
                assertions={"tempo_bounds": {"min_bpm": 60, "max_bpm": 120}},
                provenance={"operation": "muse_distill@2"},
                variation_points=[{"region": [0, 48], "kind": "ornament"}])
    delta, _ = grow_one(work, seed)
    assert delta["expansion"]["operation"] == "muse_distill@2"
    assert delta["expansion"]["variation_point_count"] == 1


def test_expansion_entry_survives_error_paths(work, monkeypatch):
    """A failed mockup build returns the error delta without an expansion
    entry — no phantom timing data on failures."""
    import muse_grow.grow as g
    monkeypatch.setattr(g, "MOCKUP_FN", lambda w: 1 / 0)
    delta, stand_in = g.grow_one(work, None)
    assert "error" in delta
    assert "expansion" not in delta


def test_growing_verdict_on_increased_trait(work):
    delta, _ = grow_one(work, None)
    prior = {"params": {"dynamics": {"velocity_pstdev": delta["params"]["dynamics"]["velocity_pstdev"] - 0.5}},
             "articulation": {"rubato_pstdev_ms": 0},
             "tempo": {"default_bpm": delta["params"]["tempo"]["default_bpm"]},
             "interpretation": {"tempo_curve_shape": "flat"},
             "provenance": {"note_count": delta["provenance"]["note_count"]}}
    report = compare_deltas(delta, prior, "x")
    assert report.traits["velocity_pstdev"]["verdict"] == "growing"
    assert report.traits["velocity_pstdev"]["delta"] == 0.5


def test_flat_verdict_on_unchanged(work):
    delta, _ = grow_one(work, None)
    report = compare_deltas(delta, delta, "x")
    assert report.traits["velocity_pstdev"]["verdict"] == "flat"
    assert report.traits["tempo_curve_shape"]["verdict"] == "same"


def test_shape_change_is_changed_not_growing(work):
    delta, _ = grow_one(work, None)
    prior = json.loads(json.dumps(delta))
    prior["interpretation"]["tempo_curve_shape"] = "arch"
    report = compare_deltas(delta, prior, "x")
    assert report.traits["tempo_curve_shape"]["verdict"] == "changed"


def test_deterministic_report(work):
    d1, _ = grow_one(work, None)
    d2, _ = grow_one(work, None)
    r1 = compare_deltas(d1, d2, "x")
    r2 = compare_deltas(d1, d2, "x")
    assert r1.to_json() == r2.to_json()


def test_cli_delta_and_report(tmp_path):
    d1 = tmp_path / "d1.json"
    subprocess.run([sys.executable, CLI, os.path.relpath(WORK, REPO), "--out", str(d1)],
                   capture_output=True, check=True)
    assert json.loads(d1.read_text())["provenance"]["note_count"] == 279
    # with a prior, the report goes to stderr and delta to stdout
    proc = subprocess.run(
        [sys.executable, CLI, os.path.relpath(WORK, REPO), "--prior", str(d1)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["provenance"]["note_count"] == 279
    assert set(json.loads(proc.stderr)["traits"])

def test_cli_persists_expansion_entry(tmp_path):
    """Spec gap 1: the written delta file carries the expansion entry."""
    out = tmp_path / "d.json"
    subprocess.run([sys.executable, CLI, os.path.relpath(WORK, REPO), "--out", str(out)],
                   capture_output=True, check=True)
    exp = json.loads(out.read_text())["expansion"]
    assert exp["operation"] == "muse_grow@1"
    assert exp["expansion_time_ms"] >= 0
    assert exp["note_count"] == 279


def test_expansion_entry_excluded_from_trait_compare(work):
    """Spec gap 2 (as the behavior stands): compare_deltas ignores the
    expansion entry — it is measurement, not a growth trait."""
    delta, _ = grow_one(work, None)
    prior = {"params": {"dynamics": {"velocity_pstdev": 0.0}},
             "articulation": {"rubato_pstdev_ms": 0.0},
             "tempo": {"default_bpm": 60.0},
             "interpretation": {"tempo_curve_shape": "flat"},
             "provenance": {"note_count": 0}}
    report = compare_deltas(delta, prior, "x")
    assert "expansion" not in report.traits
    assert "expansion" not in json.loads(report.to_json())



def test_stand_in_mockup_carries_work_ppq():
    """Stand-in mockup carries the works tick domain — bwv227.1 is ppq=2;
    the 480 default renders 240x too fast (#246 constructor sweep)."""
    m = _mockup_from_work(load(WORK))
    assert m.ppq == 2


# --- S3.8b persistence + stamping (issue #262; spec
# tests/open_20260826-004500_s3-8b-mockup-persistence.md) ---

from muse_grow.grow import persist_mockup  # noqa: E402

SEED_V2 = os.path.join(REPO, "seeds", "bwv227.1.v2.seed.yaml")
SEED_V3 = os.path.join(REPO, "seeds", "bwv227.1.v3.seed.yaml")


def test_persist_mockup_shape_and_schema(work, tmp_path):
    """Persist shape: parses as JSON and carries provenance.seed_hash of
    the driving seed's bytes. Schema-seam finding (spec item 2, pinned as
    actual): the persisted form is the dataclass dump (notes-keyed), NOT
    the session-file form (parts-keyed) — so the L1.10 validator does not
    apply here. If persist_mockup switches to the session-file shape, this
    test flips to assert validate_mockup_schema(d)."""
    from muse_mockup.schema import validate_mockup_schema, SchemaError
    m = _mockup_from_work(work)
    out = tmp_path / "w.mockup.json"
    persist_mockup(m, str(out), seed_path=SEED_V2)
    d = json.loads(out.read_text())
    expect = hashlib.sha256(open(SEED_V2, "rb").read()).hexdigest()
    assert d["provenance"]["seed_hash"] == expect
    assert "notes" in d and "parts" not in d  # dataclass-dump shape pinned
    with pytest.raises(SchemaError):
        validate_mockup_schema(d)  # session-file schema does not apply here


def test_persist_mockup_omits_seed_hash_without_seed(work, tmp_path):
    m = _mockup_from_work(work)
    out = tmp_path / "w.mockup.json"
    persist_mockup(m, str(out))
    assert "provenance" not in json.loads(out.read_text())


def test_committed_three_hop_chain_verified():
    """Known-answer pin: v3 → v2.mockup → v2 → root, all hops verified —
    drift here means a link broke; re-stamping must be deliberate."""
    from muse_lineage.lineage import walk
    hops = walk(SEED_V3, [os.path.join(REPO, "seeds")])
    assert [h.status for h in hops] == ["verified", "verified", "verified", "root"]


def test_cli_seed_mockup_out_end_to_end(tmp_path):
    """--seed + --mockup-out: mockup persisted, delta's extends matches it;
    without --mockup-out the delta has no extends (old behavior)."""
    seed_rel = os.path.relpath(SEED_V2, REPO)
    m_out = tmp_path / "w.mockup.json"
    d_out = tmp_path / "d.json"
    subprocess.run(
        [sys.executable, CLI, os.path.relpath(WORK, REPO),
         "--seed", seed_rel, "--mockup-out", str(m_out), "--out", str(d_out)],
        capture_output=True, check=True)
    assert m_out.exists()
    delta = json.loads(d_out.read_text())
    expect = hashlib.sha256(m_out.read_bytes()).hexdigest()
    assert delta["provenance"]["extends"] == expect

    d_out2 = tmp_path / "d2.json"
    subprocess.run(
        [sys.executable, CLI, os.path.relpath(WORK, REPO), "--out", str(d_out2)],
        capture_output=True, check=True)
    assert "extends" not in json.loads(d_out2.read_text())["provenance"]


def test_expansion_operation_precedence_undisturbed(work):
    """G4 precedence pin: a seed's own provenance.operation still drives
    expansion.operation — #254's stamping didn't disturb it."""
    from muse_seed import Seed
    seed = Seed(format_version="0.1", work_id="bwv227.1",
                params={"tempo": {"min_bpm": 60, "max_bpm": 120}},
                assertions={"tempo_bounds": {"min_bpm": 60, "max_bpm": 120}},
                provenance={"operation": "muse_author@3"})
    delta, _ = grow_one(work, seed)
    assert delta["expansion"]["operation"] == "muse_author@3"
