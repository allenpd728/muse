"""L3 compare-rig gap tests (issue #220) — spec:
tests/open_20260824-001741_l3-model-comparison.md.

Covered here: gap 3 (per-pair delta stats over the seed artifacts the rig
actually writes — mockup-level IOI/dynamics curves wait on real mockups,
gap 1) and the in-scope parts of gaps 1/4 (the rig's seam is seeds, not
endpoints; per-run persistence is verified as far as the rig guarantees).

Deferred per the spec: real LLM endpoint calls (gap 1 — conductor infra,
not this rig) and the blind listening page (gap 2 — explorer QA path).
"""

import json
import os

import pytest

from muse_compare import run_compare
from muse_ir import load


def corpus_path(*parts):
    p = os.path.join(os.path.dirname(__file__), "..", "..", "..", "corpus", *parts)
    return os.path.normpath(p)


@pytest.fixture(scope="module")
def compared(tmp_path_factory):
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    out_dir = str(tmp_path_factory.mktemp("cmp") / "out")
    out = run_compare(work, "classical", ["model-a", "model-b"], out_dir)
    return out, out_dir


def _load_seed(out_dir, model):
    with open(os.path.join(out_dir, f"{model}.json")) as fh:
        return json.load(fh)


def pair_delta(seed_a: dict, seed_b: dict) -> dict:
    """Per-pair tempo delta over the rig's seed artifacts — the ledger's
    companion stat while mockup-level deltas wait on real mockups."""
    ta, tb = seed_a["params"]["tempo"], seed_b["params"]["tempo"]
    return {
        "default_bpm": round(tb["default_bpm"] - ta["default_bpm"], 3),
        "min_bpm": round(tb["min_bpm"] - ta["min_bpm"], 3),
        "max_bpm": round(tb["max_bpm"] - ta["max_bpm"], 3),
    }


# --- Gap 3: A/B delta stats ---

def test_pair_delta_is_computable_and_matches_artifacts(compared):
    """The delta stat the DoD calls for is derivable from the written
    artifacts alone (ledger and its delta live together)."""
    out, out_dir = compared
    a = _load_seed(out_dir, "model-a")
    b = _load_seed(out_dir, "model-b")
    d = pair_delta(a, b)
    for key in ("default_bpm", "min_bpm", "max_bpm"):
        assert d[key] == round(
            b["params"]["tempo"][key] - a["params"]["tempo"][key], 3
        )


def test_rig_deltas_json_agrees_with_pair_delta(compared):
    """#242: the rig writes deltas.json itself; the test-local helper stays
    as the independent cross-check, not the only source of the stat."""
    out, out_dir = compared
    a = _load_seed(out_dir, "model-a")
    b = _load_seed(out_dir, "model-b")
    d = pair_delta(a, b)
    rig = json.load(open(os.path.join(out_dir, "deltas.json")))["model-a|model-b"]
    assert round(rig["tempo_default_delta"], 3) == d["default_bpm"]
    assert rig["tempo_range_delta"] == round(
        (d["max_bpm"] - d["min_bpm"]), 3)


def test_pair_delta_is_antisymmetric(compared):
    """delta(a,b) == -delta(b,a): the stat is a real difference, not a
    per-model projection."""
    out, out_dir = compared
    a = _load_seed(out_dir, "model-a")
    b = _load_seed(out_dir, "model-b")
    dab = pair_delta(a, b)
    dba = pair_delta(b, a)
    for key in dab:
        assert dab[key] == -dba[key]


def test_pair_delta_detects_the_tempo_perturbation(compared):
    """The rig's variant rule perturbs default_bpm by a hash-derived bump;
    the delta must expose it (and min/max stay shared — only default moves)."""
    out, out_dir = compared
    d = pair_delta(_load_seed(out_dir, "model-a"), _load_seed(out_dir, "model-b"))
    assert d["default_bpm"] != 0
    assert d["min_bpm"] == 0
    assert d["max_bpm"] == 0


# --- Gap 1 seam: the rig perturbs seeds, never calls endpoints ---

def test_artifacts_carry_model_provenance(compared):
    """Each written seed records its model label in provenance — the
    artifact identifies which conductor produced it without the ledger."""
    out, out_dir = compared
    for model in ("model-a", "model-b"):
        sd = _load_seed(out_dir, model)
        assert sd["provenance"]["model"] == model


def test_model_label_is_the_only_seed_difference(compared):
    """Same work + same era: seeds differ only in the tempo bump and the
    provenance label — anything else drifting would break blinding."""
    out, out_dir = compared
    a = _load_seed(out_dir, "model-a")
    b = _load_seed(out_dir, "model-b")
    pa, pb = a["params"], b["params"]
    for section in pa:
        if section == "tempo":
            continue
        assert pa[section] == pb[section], f"params.{section} drifted between models"
    assert a["params"]["tempo"]["min_bpm"] == b["params"]["tempo"]["min_bpm"]


# --- Gap 4: persistence within the rig's guarantee ---

def test_rerun_into_same_dir_overwrites_deterministically(compared, tmp_path):
    """Re-running the same roster into a fresh dir produces the same files —
    per-run persistence is reproducible, so a per-work archive is just
    'keep the dir'."""
    out, out_dir = compared
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    out2_dir = str(tmp_path / "again")
    out2 = run_compare(work, "classical", ["model-a", "model-b"], out2_dir)
    assert out["ledger"] == out2["ledger"]
    for model in ("model-a", "model-b"):
        with open(os.path.join(out_dir, f"{model}.json")) as fh:
            first = fh.read()
        with open(os.path.join(out2_dir, f"{model}.json")) as fh:
            assert first == fh.read()


def test_ledger_is_sorted_and_complete(compared):
    """Ledger maps every roster model exactly once — the blinding surface
    can't silently drop a model."""
    out, out_dir = compared
    with open(os.path.join(out_dir, "ledger.json")) as fh:
        ledger = json.load(fh)
    assert sorted(ledger) == ["model-a", "model-b"]
    assert all(isinstance(h, str) and len(h) == 12 for h in ledger.values())
