"""L3 compare-rig tests: seed variant determinism, per-model distinctness,
ledger hashing, CLI end-to-end."""

import json
import os

import pytest

from muse_compare import run_compare
from muse_ir import load


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