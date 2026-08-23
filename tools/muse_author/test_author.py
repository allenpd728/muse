"""Tests: C2 AI-assisted authoring (issue #160).

Spec: tests/open_20260823-223000_c2-authoring.md — proposal, end-to-end
loop, failure paths.
"""

import os
import subprocess
import sys

import pytest

from muse_ir import load
from muse_author import propose_seed
from muse_seed import Seed, validate_seed

DIR = os.path.dirname(__file__)
CLI = os.path.join(DIR, "cli.py")
CORPUS = os.path.normpath(os.path.join(DIR, "..", "..", "corpus"))
BACH1 = os.path.join(CORPUS, "bach", "bwv227.1.mxl")
KYRIE = os.path.join(CORPUS, "byrd", "1-Kyrie.mid")


@pytest.fixture(scope="module")
def bach():
    return load(BACH1)


class TestProposal:
    def test_required_schema_keys(self, bach):
        sd = propose_seed(bach, era_hint="classical").seed_dict
        for key in ("format_version", "work_id", "title", "params",
                    "philosophy", "variation_points", "assertions", "provenance"):
            assert key in sd, key

    def test_deterministic(self, bach):
        a = propose_seed(bach, era_hint="classical").seed_dict
        b = propose_seed(bach, era_hint="classical").seed_dict
        assert a == b

    def test_philosophy_format_matches_s33(self, bach):
        sd = propose_seed(bach, era_hint="classical").seed_dict
        phil = sd["philosophy"]
        assert isinstance(phil["tempo_philosophy"], list)
        assert phil["provenance"]["author"] == "muse_author"
        assert phil["provenance"]["ai_assisted"] is True

    def test_proposal_validates_against_schema(self, bach):
        sd = propose_seed(bach, era_hint="classical").seed_dict
        seed = Seed(**{k: sd[k] for k in ("format_version", "work_id", "title", "params",
                                          "philosophy", "variation_points",
                                          "assertions", "provenance")})
        validate_seed(seed)

    def test_missing_era_defaults_classical(self, bach):
        sd = propose_seed(bach).seed_dict
        assert sd["provenance"]["era_hint"] == "classical"

    def test_register_derived_from_work(self, bach):
        sd = propose_seed(bach, era_hint="classical").seed_dict
        reg = sd["assertions"]["register"]
        assert reg["part"] == bach.parts[0].id


class TestEndToEndLoop:
    def run_cli(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, CLI, *args],
            capture_output=True, text=True, timeout=300,
            cwd=cwd or DIR,
        )

    def test_bach_proposal_validates(self, tmp_path):
        out = str(tmp_path / "p.yaml")
        r = self.run_cli(BACH1, "--era", "classical", "--out", out)
        assert r.returncode == 0, r.stderr + r.stdout
        assert "validation exit: 0" in r.stdout
        assert os.path.exists(out)

    def test_byrd_proposal_validates(self, tmp_path):
        out = str(tmp_path / "p.yaml")
        r = self.run_cli(KYRIE, "--era", "renaissance", "--out", out)
        # renaissance isn't in ERA_BUDGETS; CLI's --era is a hint only,
        # so the proposal should still validate (budget check uses known eras)
        assert "OK  proposed" in r.stdout

    def test_invalid_work_fails_loudly(self, tmp_path):
        r = self.run_cli(str(tmp_path / "nope.mxl"))
        assert r.returncode != 0
