"""Tests: W4 diff tool (issue #133).

Spec: tests/open_20260823-191500_w4-diff-tool.md — engine correctness,
mutation behavior, tolerance semantics, CLI contract.
"""

import dataclasses
import os
import subprocess
import sys

import pytest

from muse_diff import diff
from muse_ir import load
from muse_ir.model import Meta, Note, Part, Work

DIR = os.path.dirname(__file__)
CLI = os.path.join(DIR, "cli.py")
CORPUS = os.path.normpath(os.path.join(DIR, "..", "..", "corpus"))


def make_work(notes):
    return Work(
        parts=[Part(id="P1", name="P1", notes=list(notes))],
        meta=Meta(source_format="musicxml", ppq=480),
    )


KYRIE = os.path.join(CORPUS, "byrd", "1-Kyrie.mid")
BACH1 = os.path.join(CORPUS, "bach", "bwv227.1.mxl")
BACH3 = os.path.join(CORPUS, "bach", "bwv227.3.mxl")


@pytest.fixture(scope="module")
def kyrie():
    return load(KYRIE)


class TestEngineCorrectness:
    def test_self_diff_is_perfect(self, kyrie):
        report = diff(kyrie, kyrie)
        assert report.recall == 1.0
        assert report.precision == 1.0
        assert report.matched == kyrie.note_count
        assert report.mismatches == []

    def test_pairing_is_deterministic(self, kyrie):
        reports = [diff(kyrie, kyrie) for _ in range(10)]
        for r in reports:
            assert (r.recall, r.precision, r.matched) == (1.0, 1.0, kyrie.note_count)

    def test_rests_participate_in_matching(self):
        a = make_work([Note(pitch=None, onset=0, duration=480),
                       Note(pitch=60, onset=480, duration=480)])
        same = make_work([Note(pitch=60, onset=480, duration=480),
                          Note(pitch=None, onset=0, duration=480)])
        missing_rest = make_work([Note(pitch=60, onset=480, duration=480)])
        assert diff(a, same).ok()
        report = diff(a, missing_rest)
        assert report.recall == 0.5
        kinds = [m.kind for m in report.mismatches]
        assert kinds == ["missing"]

    def test_unpitched_participate_in_matching(self):
        a = make_work([Note(pitch=None, onset=0, duration=240, notations=frozenset({"unpitched"})),
                       Note(pitch=64, onset=240, duration=240)])
        b = make_work([Note(pitch=None, onset=0, duration=240, notations=frozenset({"unpitched"})),
                       Note(pitch=64, onset=240, duration=240)])
        assert diff(a, b).ok()


class TestMutationBehavior:
    def test_deletion_degrades_recall_only(self, kyrie):
        mutant = make_work([n for p in kyrie.parts for n in p.notes][:10])
        report = diff(kyrie, mutant)
        assert report.recall == pytest.approx(10 / kyrie.note_count)
        assert report.precision == 1.0
        assert all(m.kind == "missing" for m in report.mismatches)

    def test_insertion_degrades_precision_only(self, kyrie):
        flat = [dataclasses.replace(n, onset=n.onset) for p in kyrie.parts for n in p.notes]
        flat.append(Note(pitch=99, onset=999999, duration=1))
        mutant = Work(parts=[Part(id="X", name="X", notes=flat)], meta=kyrie.meta)
        report = diff(kyrie, mutant)
        assert report.recall == 1.0
        assert report.precision == pytest.approx(kyrie.note_count / (kyrie.note_count + 1))
        assert [m.kind for m in report.mismatches] == ["extra"]

    def test_onset_drift_within_tolerance_is_not_missing(self):
        a = make_work([Note(pitch=60, onset=100, duration=480)])
        b = make_work([Note(pitch=60, onset=104, duration=480)])
        report = diff(a, b, tolerance_ticks=8)
        assert report.matched == 1
        assert report.ok()  # drift within tolerance is acceptable, but recorded
        kinds = [m.kind for m in report.mismatches]
        assert kinds == ["onset-drift"]
        assert "missing" not in kinds and "extra" not in kinds

    def test_velocity_mismatch_classified(self):
        a = make_work([Note(pitch=60, onset=0, duration=480, velocity=80)])
        b = make_work([Note(pitch=60, onset=0, duration=480, velocity=64)])
        report = diff(a, b)
        assert [m.kind for m in report.mismatches] == ["velocity-drift"]
        assert report.matched == 1

    def test_one_sided_velocity_not_drift(self):
        a = make_work([Note(pitch=60, onset=0, duration=480, velocity=None)])
        b = make_work([Note(pitch=60, onset=0, duration=480, velocity=64)])
        assert diff(a, b).mismatches == []


class TestToleranceSemantics:
    def test_zero_tolerance_requires_exact_ticks(self):
        a = make_work([Note(pitch=60, onset=100, duration=480)])
        b = make_work([Note(pitch=60, onset=101, duration=480)])
        report = diff(a, b, tolerance_ticks=0)
        assert report.matched == 0
        assert {m.kind for m in report.mismatches} == {"missing", "extra"}

    def test_boundary_is_inclusive(self):
        a = make_work([Note(pitch=60, onset=100, duration=480)])
        b = make_work([Note(pitch=60, onset=108, duration=480)])
        assert diff(a, b, tolerance_ticks=8).matched == 1
        assert diff(a, b, tolerance_ticks=7).matched == 0


class TestCLI:
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, CLI, *args],
            capture_output=True, text=True, timeout=600,
            cwd=os.path.join(DIR, ".."),
        )

    def test_identical_files_exit_zero(self):
        r = self.run_cli(KYRIE, KYRIE)
        assert r.returncode == 0
        assert "recall" in r.stdout and "precision" in r.stdout

    def test_different_files_exit_one(self):
        r = self.run_cli(BACH1, BACH3)
        assert r.returncode == 1

    def test_self_test_exits_zero(self):
        r = self.run_cli("--self-test")
        assert r.returncode == 0

    def test_mismatch_list_capped_at_20(self):
        r = self.run_cli(BACH1, BACH3)
        lines = [ln for ln in r.stdout.splitlines() if ln.lstrip().startswith(("missing", "extra"))]
        assert len(lines) <= 20
