"""Tests: C1 seed validator CLI (issue #161).

Spec: tests/open_20260823-220000_c1-seed-validator.md — commands,
failure paths, era-budget check.
"""

import os
import subprocess
import sys

import pytest

DIR = os.path.dirname(__file__)
CLI = os.path.join(DIR, "cli.py")
REPO = os.path.normpath(os.path.join(DIR, "..", ".."))
EXAMPLE = os.path.join(REPO, "seeds", "bwv227.1.seed.yaml")
BACH1 = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")

VALID_SEED = """\
format_version: '0.1'
work_id: bwv227.1
params:
  tempo: {min_bpm: 62, max_bpm: 129, default_bpm: 96}
assertions:
  register: {part: P4, min: C2, max: C4}
provenance:
  source: corpus/bach/bwv227.1.mxl
  author: tester
  ai_assisted: true
"""


def run_cli(*args):
    return subprocess.run(
        [sys.executable, CLI, *args],
        capture_output=True, text=True, timeout=300,
    )


def write_seed(tmp_path, text=VALID_SEED):
    p = tmp_path / "s.yaml"
    p.write_text(text)
    return str(p)


class TestRead:
    def test_read_prints_seed_summary(self):
        r = run_cli("read", EXAMPLE)
        assert r.returncode == 0, r.stderr
        assert "work_id: bwv227.1" in r.stdout
        assert "params:" in r.stdout
        assert "assertions:" in r.stdout

    def test_read_malformed_fails(self, tmp_path):
        r = run_cli("read", write_seed(tmp_path, "not: [valid"))
        assert r.returncode == 1


class TestValidate:
    def test_valid_seed_passes(self, tmp_path):
        r = run_cli("validate", write_seed(tmp_path), BACH1)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "OK  seed schema valid" in r.stdout
        assert "OK  assertions pass on work" in r.stdout
        assert "OK  seed validates against work" in r.stdout

    def test_example_seed_passes(self):
        r = run_cli("validate", EXAMPLE, BACH1)
        assert r.returncode == 0, r.stdout

    def test_malformed_seed_fails(self, tmp_path):
        bad = "format_version: '0.1'\nwork_id: x\n"
        r = run_cli("validate", write_seed(tmp_path, bad), BACH1)
        assert r.returncode == 1
        assert "FAIL" in r.stdout

    def test_violated_assertions_fail(self, tmp_path):
        bad = VALID_SEED.replace("max: C4", "max: A2")
        r = run_cli("validate", write_seed(tmp_path, bad), BACH1)
        assert r.returncode == 1
        assert "register" in r.stdout


class TestBudgetCheck:
    @pytest.mark.parametrize("era", ["baroque", "classical", "romantic", "early_romantic"])
    def test_known_eras(self, era):
        r = run_cli("budget-check", era)
        assert r.returncode == 0
        assert era in r.stdout
        assert "chord spread" in r.stdout

    def test_unknown_era_rejected_by_argparse(self):
        r = run_cli("budget-check", "medieval")
        assert r.returncode != 0  # argparse choices reject


class TestEraBudgetCheck:
    def test_era_in_provenance_checked(self, tmp_path):
        seeded = VALID_SEED.replace("author: tester", "author: tester\n  era: classical")
        r = run_cli("validate", write_seed(tmp_path, seeded), BACH1)
        assert "within classical budget" in r.stdout

    def test_era_missing_skipped(self, tmp_path):
        r = run_cli("validate", write_seed(tmp_path), BACH1)
        assert "budget" not in r.stdout.lower() or "WARN" not in r.stdout

    def test_excessive_range_warns(self, tmp_path):
        seeded = (VALID_SEED
                  .replace("author: tester", "author: tester\n  era: baroque")
                  .replace("min_bpm: 62", "min_bpm: 40"))
        r = run_cli("validate", write_seed(tmp_path, seeded), BACH1)
        assert "outside baroque budget" in r.stdout
