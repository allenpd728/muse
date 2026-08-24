"""L3 compare-rig tests: seed variant determinism, per-model distinctness,
ledger hashing, deltas.json layer (#242), CLI end-to-end."""

import json
import os
import subprocess
import sys

import pytest

from muse_compare import run_compare
from muse_compare.compare import delta_stats, make_seeds_for_models
from muse_ir import load

TOOLS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def corpus_path(*parts):
    p = os.path.join(os.path.dirname(__file__), "..", "..", "..", "corpus", *parts)
    return os.path.normpath(p)


def test_seeds_are_deterministic(tmp_path):
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    out = run_compare(work, "classical", ["a", "b"], str(tmp_path / "c"))
    out2 = run_compare(work, "classical", ["a", "b"], str(tmp_path / "c2"))
    assert out["ledger"] == out2["ledger"]


def test_models_produce_distinct_hashes(tmp_path):
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    out = run_compare(work, "classical", ["model-x", "model-y"], str(tmp_path / "c"))
    assert out["ledger"]["model-x"] != out["ledger"]["model-y"]


def test_artifacts_written(tmp_path):
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    out_dir = str(tmp_path / "c")
    run_compare(work, "classical", ["m1", "m2", "m3"], out_dir)
    for m in ["m1", "m2", "m3"]:
        assert os.path.exists(os.path.join(out_dir, f"{m}.json"))
    assert os.path.exists(os.path.join(out_dir, "ledger.json"))


def test_ledger_hashes_match_files(tmp_path):
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    out_dir = str(tmp_path / "c")
    run_compare(work, "classical", ["a", "b"], out_dir)
    ledger = json.load(open(os.path.join(out_dir, "ledger.json")))
    from compare import _hash_seed
    for m in ["a", "b"]:
        data = json.load(open(os.path.join(out_dir, f"{m}.json")))
        assert _hash_seed(data) == ledger[m]


def test_single_model_still_works(tmp_path):
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    out = run_compare(work, "classical", ["solo"], str(tmp_path / "c"))
    assert out["models"] == ["solo"]


class TestDeltaStats:
    """deltas.json — the derived stats DoD #195 pairs with the ledger
    (#242). Params-level until a real harness plugs the mockup seam."""

    def test_pair_keys_and_count(self, tmp_path):
        work = load(corpus_path("bach", "bwv227.1.mxl"))
        out = run_compare(work, "classical", ["a", "b", "c"], str(tmp_path / "c"))
        assert set(out["deltas"]) == {"a|b", "a|c", "b|c"}

    def test_delta_values_match_seeds(self, tmp_path):
        work = load(corpus_path("bach", "bwv227.1.mxl"))
        seeds = make_seeds_for_models(work, "classical", ["alpha", "beta"])
        deltas = delta_stats(seeds)
        expected = (seeds["beta"]["params"]["tempo"]["default_bpm"]
                    - seeds["alpha"]["params"]["tempo"]["default_bpm"])
        assert deltas["alpha|beta"]["tempo_default_delta"] == expected
        # Current perturbation rule nudges only the tempo default.
        assert deltas["alpha|beta"]["tempo_range_delta"] == 0
        assert deltas["alpha|beta"]["tempo_flex_delta"] == 0
        assert deltas["alpha|beta"]["density_range_delta"] == 0

    def test_deltas_deterministic(self, tmp_path):
        work = load(corpus_path("bach", "bwv227.1.mxl"))
        a = run_compare(work, "classical", ["x", "y"], str(tmp_path / "1"))
        b = run_compare(work, "classical", ["x", "y"], str(tmp_path / "2"))
        assert a["deltas"] == b["deltas"]

    def test_deltas_json_written(self, tmp_path):
        work = load(corpus_path("bach", "bwv227.1.mxl"))
        out_dir = str(tmp_path / "c")
        out = run_compare(work, "classical", ["a", "b"], out_dir)
        on_disk = json.load(open(os.path.join(out_dir, "deltas.json")))
        assert on_disk == out["deltas"]

    def test_single_model_has_no_pairs(self, tmp_path):
        work = load(corpus_path("bach", "bwv227.1.mxl"))
        out = run_compare(work, "classical", ["solo"], str(tmp_path / "c"))
        assert out["deltas"] == {}


def test_cli_end_to_end(tmp_path):
    env = dict(os.environ, PYTHONPATH=TOOLS)
    out_dir = str(tmp_path / "cli")
    proc = subprocess.run(
        [sys.executable, "-m", "muse_compare",
         corpus_path("bach", "bwv227.1.mxl"),
         "--models", "stub-a,stub-b", "--era", "classical",
         "--out-dir", out_dir],
        capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 0, proc.stderr[:300]
    assert "stub-a" in proc.stdout and "stub-b" in proc.stdout
    ledger = json.load(open(os.path.join(out_dir, "ledger.json")))
    assert set(ledger) == {"stub-a", "stub-b"}
    assert os.path.exists(os.path.join(out_dir, "deltas.json"))