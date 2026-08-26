"""R2 rehearsal-directive tests (spec: tests/open_20260826-110000_r2-rehearsal-pane.md)."""

import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_ir import load as load_work  # noqa: E402
from muse_seed import load_seed  # noqa: E402
from muse_rehearse import (  # noqa: E402
    DirectiveError, parse_directive, compile_directive, dry_run,
    commit_directive,
)
from muse_rehearse.rehearse import bar_onsets  # noqa: E402
from muse_lineage.lineage import walk, sha256_file  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WORK_PATH = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")
SEED_PATH = os.path.join(REPO, "seeds", "bwv227.1.v2.seed.yaml")


@pytest.fixture(scope="module")
def work():
    return load_work(WORK_PATH)


@pytest.fixture(scope="module")
def base_seed():
    return load_seed(open(SEED_PATH).read(), fmt="yaml")


# --- 1. grammar accept/reject matrix ---

@pytest.mark.parametrize("text,verb,changed", [
    ("rebalance: bring P1 up at ticks 480-960", "rebalance", "params"),
    ("phrase: quieter into development", "phrase", "variation_points"),
    ("tempo_arch: wider", "tempo_arch", "params"),
    ("rubato: more", "rubato", "params"),
    ("hold: ticks 0-480", "hold", "assertions"),
])
def test_verbs_compile_to_documented_knobs(base_seed, text, verb, changed):
    d = parse_directive(text, seed=base_seed)
    assert d.verb == verb
    cand, diff = dry_run(d, base_seed)
    assert changed in diff["changes"], f"{verb} should change {changed}"


def test_unknown_verb_rejected(base_seed):
    with pytest.raises(DirectiveError, match="unknown verb"):
        parse_directive("orchestrate: make it brassier", seed=base_seed)


def test_two_verbs_rejected(base_seed):
    with pytest.raises(DirectiveError, match="one verb per directive"):
        parse_directive("rebalance: P1 up and tempo_arch wider", seed=base_seed)


def test_unknown_part_rejected(base_seed, work):
    with pytest.raises(DirectiveError, match="unknown part"):
        parse_directive("rebalance: P99 louder at ticks 0-10", seed=base_seed, work=work)


# --- 2. region resolution: bar / tick / label ---

def test_bar_reference_resolves_via_meter_map(base_seed, work):
    d = parse_directive("phrase: quieter at bar 5", seed=base_seed, work=work)
    assert d.region == (32, 40)  # 4/4, ppq 2 → 8 ticks/bar


def test_bar_range_resolves(base_seed, work):
    d = parse_directive("phrase: quieter at bars 5-7", seed=base_seed, work=work)
    assert d.region == (32, 56)


def test_bar_out_of_range_rejected(base_seed, work):
    with pytest.raises(DirectiveError, match="out of range"):
        parse_directive("phrase: quieter at bar 99", seed=base_seed, work=work)


def test_bar_without_work_rejected(base_seed):
    with pytest.raises(DirectiveError, match="needs the work"):
        parse_directive("phrase: quieter at bar 5", seed=base_seed)


def test_tick_region_passthrough(base_seed):
    d = parse_directive("hold: ticks 480-960", seed=base_seed)
    assert d.region == (480, 960)


def test_bar_onsets_meter_changes(work):
    """Byrd Kyrie has mid-piece meter changes; onsets must track them."""
    byrd = load_work(os.path.join(REPO, "corpus", "byrd", "1-Kyrie.mid"))
    onsets = bar_onsets(byrd)
    assert onsets[:3] == [0, 2304, 3840]  # 12/4 then 8/4 at ppq 192


# --- 3. dry-run = param_diff, no mockup ---

def test_dry_run_writes_nothing(base_seed, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = parse_directive("tempo_arch: wider", seed=base_seed)
    _, diff = dry_run(d, base_seed)
    assert diff["status"] == "compared"
    assert os.listdir(tmp_path) == []  # no files written


# --- 4. lineage-root semantics ---

def test_commit_writes_directive_and_stamps_lineage(base_seed, work, tmp_path):
    import shutil
    seeds = tmp_path / "seeds"
    seeds.mkdir()
    base_copy = seeds / "bwv227.1.v2.seed.yaml"
    shutil.copy(SEED_PATH, str(base_copy))
    d = parse_directive("phrase: quieter at bar 8", work=work)
    dpath, spath = commit_directive(d, str(base_copy), "quieter-bar-8",
                                    repo_root=str(tmp_path), work=work)
    assert dpath.endswith(".directive.txt")
    rev = yaml.safe_load(open(spath))
    assert rev["provenance"]["extends"] == sha256_file(dpath)
    assert rev["provenance"]["operation"] == "muse_rehearse@1"
    # walk resolves revision → directive (root), directive itself has no parent
    hops = walk(spath, [str(tmp_path / "seeds")])
    assert [h.status for h in hops] == ["verified", "root"]


# --- 5. budget clamping ---

def test_degree_clamps_to_budget(base_seed):
    d = parse_directive("rebalance: P1 up 95% at ticks 0-10", seed=base_seed)
    cand = compile_directive(d, base_seed)
    assert cand.params["part_gains"]["P1"] <= 2.0


# --- 7. no auto-commit ---

def test_parse_and_dry_run_write_nothing(base_seed, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = parse_directive("hold: ticks 0-10", seed=base_seed)
    dry_run(d, base_seed)
    assert os.listdir(tmp_path) == []
