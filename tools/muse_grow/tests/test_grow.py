"""Growth harness tests (issue #203).

The report's trait verdicts are computed correctly; the stand-in is
marked; the CLI emits delta + report deterministically.
"""

import json
import os
import subprocess
import sys

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


def test_stand_in_mockup_carries_work_ppq():
    """Stand-in mockup carries the works tick domain — bwv227.1 is ppq=2;
    the 480 default renders 240x too fast (#246 constructor sweep)."""
    m = _mockup_from_work(load(WORK))
    assert m.ppq == 2
