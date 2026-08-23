"""E2E chain harness tests (issue #162).

Stages compose per work; failure isolates the stage; determinism holds.
"""

import os
import subprocess
import sys

import pytest

from muse_chain import ChainResult, StageResult, run_work
from muse_chain.chain import (
    _stage_container,
    _stage_pack,
    check_determinism,
)

SMALL = [("bach-bwv227.1", "bach/bwv227.1.mxl"),
         ("byrd-1-kyrie", "byrd/1-Kyrie.mid")]


class TestStagesCompose:
    @pytest.mark.parametrize("wid,rel", SMALL)
    def test_full_chain_green(self, wid, rel):
        r = run_work(wid, rel)
        assert r.ok
        stages = {s.stage.split("(")[0]: s.status for s in r.stages}
        for stage in ("parse", "pack", "container", "decode", "verify"):
            assert stages[stage] == "PASS", stage
        assert stages["render"] == "SKIP"

    def test_artifacts_present_and_bytes(self):
        r = run_work(*SMALL[0])
        assert set(r.artifacts) == {"roll.bin", "manifest.json"}
        assert r.artifacts["roll.bin"].startswith(b"MUR1")
        assert r.artifacts["manifest.json"].startswith(b"{")

    def test_verify_skips_over_budget(self):
        r = run_work("beethoven-sym9", "beethoven/beethoven-sym9.xml")
        assert r.ok
        verify = next(s for s in r.stages if s.stage.startswith("verify"))
        assert verify.status == "SKIP"
        decode = next(s for s in r.stages if s.stage.startswith("decode"))
        assert decode.status == "PASS"  # structural check carries the load


class TestFailureIsolation:
    def test_missing_file_fails_at_parse(self):
        r = run_work("nope", "bach/nope.mxl")
        assert not r.ok
        fails = [s for s in r.stages if s.status == "FAIL"]
        assert len(fails) == 1
        assert fails[0].stage.startswith("parse")

    def test_stage_names_carry_task_nouns(self):
        r = run_work(*SMALL[0])
        for s in r.stages:
            assert "(" in s.stage and ")" in s.stage  # e.g. parse(W1)


class TestDeterminism:
    def test_two_runs_identical_artifacts(self):
        mismatches = check_determinism(registry=SMALL)
        assert mismatches == []

    def test_pack_deterministic_on_rich_work(self):
        from muse_ir import load
        work = load(os.path.join(
            os.path.dirname(__file__), "..", "..", "corpus", SMALL[1][1]))
        roll, s = _stage_pack(work)
        assert s.status == "PASS"
        assert roll == _stage_pack(work)[0]


class TestCLI:
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "cli.py"), *args],
            capture_output=True, text=True, timeout=900,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )

    def test_single_work_exit_zero(self):
        r = self.run_cli("--work", "bach/bwv227.1.mxl")
        assert r.returncode == 0
        assert r.stdout.count("OK") >= 5
        assert "SKIP" in r.stdout

    def test_determinism_flag(self):
        r = self.run_cli("--determinism")
        assert r.returncode == 0
        assert "identical artifacts" in r.stdout
