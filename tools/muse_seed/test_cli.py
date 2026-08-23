"""C1 CLI tests (issue #148): validate seed files against corpus works.

End-to-end: schema (S3.1) → budgets (S3.2) → philosophy (S3.3) →
variation points (S3.4) → assertions against the loaded work (S3.5).
"""

import os
import subprocess
import sys

import pytest

DIR = os.path.dirname(__file__)
CLI = os.path.join(DIR, "cli.py")
REPO = os.path.normpath(os.path.join(DIR, "..", ".."))
EXAMPLE = os.path.join(REPO, "seeds", "bwv227.1.seed.yaml")
BACH3 = os.path.join(REPO, "corpus", "bach", "bwv227.3.mxl")

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
        cwd=REPO,
    )


def write_seed(tmp_path, text=VALID_SEED, name="s.yaml"):
    p = tmp_path / name
    p.write_text(text)
    return str(p)


class TestValidateHappyPath:
    def test_example_seed_validates_end_to_end(self):
        r = run_cli("validate", EXAMPLE)
        assert r.returncode == 0, r.stderr
        for stage in ("schema", "budgets", "assertions"):
            assert stage in r.stdout
        assert "VALID" in r.stdout

    def test_inline_seed_validates(self, tmp_path):
        r = run_cli("validate", write_seed(tmp_path))
        assert r.returncode == 0, r.stderr

    def test_assertion_failure_invalid(self, tmp_path):
        bad = VALID_SEED.replace("max: C4", "max: A2")  # P4 goes below A2
        r = run_cli("validate", write_seed(tmp_path, bad))
        assert r.returncode == 1
        assert "INVALID" in r.stderr
        assert "register" in r.stderr

    def test_work_override(self, tmp_path):
        # bwv227.3's P4 spans E2..E4; widen the register for the override
        wider = VALID_SEED.replace("max: C4", "max: G4")
        r = run_cli("validate", write_seed(tmp_path, wider), "--work", BACH3)
        assert r.returncode == 0, r.stderr
        assert "bwv227.3.mxl" in r.stdout


class TestBudgetChecks:
    def test_excessive_tempo_range_rejected(self, tmp_path):
        bad = VALID_SEED.replace("min_bpm: 62", "min_bpm: 10")
        r = run_cli("validate", write_seed(tmp_path, bad))
        assert r.returncode == 1
        assert "exceeds every era budget" in r.stderr

    def test_default_outside_range_rejected(self, tmp_path):
        bad = VALID_SEED.replace("default_bpm: 96", "default_bpm: 200")
        r = run_cli("validate", write_seed(tmp_path, bad))
        assert r.returncode == 1


class TestSchemaFailures:
    def test_missing_file(self):
        r = run_cli("validate", "seeds/nope.yaml")
        assert r.returncode == 1
        assert "cannot read" in r.stderr

    def test_garbage_yaml(self, tmp_path):
        r = run_cli("validate", write_seed(tmp_path, "not: [valid"))
        assert r.returncode == 1

    def test_bad_philosophy_invalid(self, tmp_path):
        bad = VALID_SEED + (
            "philosophy:\n  tempo_philosophy: [in the manner of Glenn Gould]\n"
            "  provenance: {author: tester, ai_assisted: true}\n"
        )
        r = run_cli("validate", write_seed(tmp_path, bad))
        assert r.returncode == 1
        assert "Glenn Gould" in r.stderr

    def test_bad_variation_point_invalid(self, tmp_path):
        bad = VALID_SEED + (
            "variation_points:\n  - {region: [0, 999999], kind: ornament}\n"
        )
        r = run_cli("validate", write_seed(tmp_path, bad))
        assert r.returncode == 1
        assert "exceeds work duration" in r.stderr


class TestShow:
    def test_show_emits_canonical_seed(self, tmp_path):
        r = run_cli("show", write_seed(tmp_path))
        assert r.returncode == 0
        assert "work_id: bwv227.1" in r.stdout
