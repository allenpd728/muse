"""R3 study-script + survival-feedback tests (spec: tests/open_*_r3-study.md)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_ir import load as load_work  # noqa: E402
from muse_seed import load_seed  # noqa: E402
from muse_study import SCRIPTS, run_script, check_survival  # noqa: E402
from muse_study.study import Step, _seed_survival  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WORK_PATH = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")
SEED_PATH = os.path.join(REPO, "seeds", "bwv227.1.v2.seed.yaml")


@pytest.fixture(scope="module")
def work():
    return load_work(WORK_PATH)


@pytest.fixture(scope="module")
def base_seed():
    return load_seed(open(SEED_PATH).read(), fmt="yaml")


def test_scripts_have_steps_and_issues():
    for name, s in SCRIPTS.items():
        assert s.steps, f"{name}: no steps"
        assert s.issue, f"{name}: no issue text"
        for step in s.steps:
            verb = step.directive.split(":")[0].split()[0]
            assert verb in ("rebalance", "phrase", "tempo_arch", "rubato", "hold"), \
                f"{name}: step uses non-grammar verb {verb}"


def test_run_script_reports_per_step(base_seed, work):
    _, reports = run_script(SCRIPTS["quiet-the-bass"], SEED_PATH, work=work)
    assert len(reports) == len(SCRIPTS["quiet-the-bass"].steps)
    assert all(r.verb == "rebalance" for r in reports)
    assert all(r.verdict in ("moved", "flat", "drifted", "unmeasurable")
               for r in reports)


def test_survival_rebalance_moves_part_gains(base_seed):
    step = Step("rebalance: bring P4 down")
    from muse_rehearse import parse_directive, compile_directive
    d = parse_directive(step.directive, seed=base_seed)
    cand = compile_directive(d, base_seed)
    rep = check_survival(step, base_seed, cand, None, None)
    assert rep.verdict == "moved"
    assert rep.candidate_value["P4"] < 1.0  # down reduces gain


def test_survival_direction_sign(base_seed):
    """A 'down' directive must lower the gain, not raise it (regression:
    direction word order made 'bring … down' parse as up)."""
    from muse_rehearse import parse_directive, compile_directive
    d = parse_directive("rebalance: bring P4 down", seed=base_seed)
    cand = compile_directive(d, base_seed)
    assert cand.params["part_gains"]["P4"] < 1.0


def test_seed_survival_phrase_counts_variation_points(base_seed):
    from muse_rehearse import parse_directive, compile_directive
    d = parse_directive("phrase: quieter into development", seed=base_seed)
    cand = compile_directive(d, base_seed)
    b, c, verdict = _seed_survival("phrase", base_seed, cand)
    assert verdict == "moved" and c == b + 1


def test_hold_survival_adds_tempo_bounds(base_seed):
    from muse_rehearse import parse_directive, compile_directive
    d = parse_directive("hold: ticks 0-480", seed=base_seed)
    cand = compile_directive(d, base_seed)
    _, has, verdict = _seed_survival("hold", base_seed, cand)
    assert verdict == "moved" and has is True


def test_flat_when_nothing_changes(base_seed):
    b, c, verdict = _seed_survival("rebalance", base_seed, base_seed)
    assert verdict == "flat"
