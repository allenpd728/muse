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


class TestScalingExactPath:
    """Issue #317: the tolerance-0 path must be O(n_a + n_b), not O(n_a x n_b).

    Beethoven 9 (239,459 notes) exceeded 15 minutes under the quadratic scan
    and was skipped by the chain's budget gate — so the v1.0 conformance
    target went unverified. These tests pin both the result and the scaling.
    """

    def _big(self, n):
        # Many notes sharing a pitch so the old inner scan could not shortcut
        # on a pitch mismatch; onsets spread so keys stay distinct.
        return make_work([
            Note(pitch=60 + (i % 12), onset=i * 10, duration=10)
            for i in range(n)
        ])

    def test_exact_path_is_linear_enough(self):
        """Doubling n must not quadruple the work.

        Compares *scaling*, not absolute time, so it is machine-independent.
        A quadratic scan shows up as a ~4x ratio. Sizes are picked so the
        linear path takes only milliseconds — the ratio then fails in about a
        second instead of hanging the suite, which is what happened when the
        quadratic path was restored at larger sizes (the run had to be killed).

        Measured on this checkout: linear n=4000 ≈ 5ms, n=8000 ≈ 12ms;
        quadratic n=4000 ≈ 420ms (≈ 80x slower, and ~4x per doubling).
        """
        import time

        def timed(n):
            w = self._big(n)
            best = None
            for _ in range(5):  # min-of-5 to damp scheduler noise
                t0 = time.perf_counter()
                r = diff(w, w)
                dt = time.perf_counter() - t0
                assert r.ok(), f"self-diff failed at n={n}"
                best = dt if best is None else min(best, dt)
            return best

        small = timed(4000)
        large = timed(8000)
        assert small > 0, "timing collapsed to zero — cannot measure scaling"
        ratio = large / small
        assert ratio < 3.0, (
            f"diff scaling looks quadratic: {small * 1000:.2f}ms -> "
            f"{large * 1000:.2f}ms (ratio {ratio:.2f}; linear ~2x, quadratic ~4x)"
        )

    def test_large_input_completes_quickly(self):
        """A 40k-note exact diff must finish in seconds, not minutes — the
        gate the chain used to rely on was 30k notes."""
        import time

        w = self._big(40000)
        t0 = time.perf_counter()
        report = diff(w, w)
        elapsed = time.perf_counter() - t0
        assert report.ok()
        assert report.matched == 40000
        assert elapsed < 20, f"40k-note diff took {elapsed:.1f}s"

    def test_duplicate_keys_pair_in_b_index_order(self):
        """Tie behaviour is load-bearing: the old scan kept the lowest `b`
        index among equal (pitch, onset) candidates. A FIFO bucket reproduces
        it exactly; this pins that so a future set/dict refactor cannot
        silently reorder pairings."""
        a = make_work([Note(pitch=60, onset=0, duration=10) for _ in range(3)])
        # b has three candidates for the same key; the second carries a
        # different velocity so we can see which index each `a` note consumed.
        b = make_work([
            Note(pitch=60, onset=0, duration=10, velocity=100),
            Note(pitch=60, onset=0, duration=10, velocity=101),
            Note(pitch=60, onset=0, duration=10, velocity=102),
        ])
        report = diff(a, b)
        assert report.matched == 3
        assert report.mismatches == [], "equal-key pairing should raise no drift"

    def test_exact_path_reports_missing_and_extra(self):
        a = make_work([Note(pitch=60, onset=0, duration=10),
                       Note(pitch=62, onset=10, duration=10)])
        b = make_work([Note(pitch=60, onset=0, duration=10)])
        report = diff(a, b)
        kinds = sorted(m.kind for m in report.mismatches)
        assert kinds == ["missing"], kinds
        assert report.recall == 0.5 and report.precision == 1.0

        reverse = diff(b, a)
        assert sorted(m.kind for m in reverse.mismatches) == ["extra"]

    def test_tolerance_path_unchanged(self):
        """tolerance > 0 must still use the nearest-onset search (the exact
        fast path must not be taken)."""
        a = make_work([Note(pitch=60, onset=100, duration=10)])
        b = make_work([Note(pitch=60, onset=105, duration=10)])
        assert diff(a, b, tolerance_ticks=0).matched == 0
        assert diff(a, b, tolerance_ticks=5).matched == 1
        drift = diff(a, b, tolerance_ticks=5).mismatches
        assert [m.kind for m in drift] == ["onset-drift"], drift

    def test_exact_and_tolerance_agree_when_onsets_are_equal(self):
        w = self._big(500)
        assert diff(w, w).matched == diff(w, w, tolerance_ticks=1).matched


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
