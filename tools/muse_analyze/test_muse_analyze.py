"""Tests: W3 pattern analyzer (issue #136).

Spec: tests/open_20260823-204500_w3-pattern-analyzer.md — pattern-class pins,
scale-budget ladder, delta curve, CLI per-work and --all.

Pins measured 2026-08-23 (muse_analyze on tools/ir). Exact pins use ==;
counts are evidence for S-series constructs and must not drift silently.
"""

import os
import subprocess
import sys
import time

import pytest

# Beethoven 9 analysis takes ~30s alone; keep the budget test but make it
# opt-in for the fast suite (CI skips via -m "not slow"; slow suites include it).
slow = pytest.mark.skipif(
    os.environ.get("MUSE_SKIP_SLOW", "").lower() in ("1", "true", "yes"),
    reason="MUSE_SKIP_SLOW set — skipping Beethoven 9 budget test (~30s)",
)

from muse_ir import load
from muse_ir.model import Meta, Note, Part, Work
from muse_analyze import analyze
from muse_analyze.patterns import _find_repeats, _find_transposed

DIR = os.path.dirname(__file__)
CLI = os.path.join(DIR, "cli.py")
CORPUS = os.path.normpath(os.path.join(DIR, "..", "..", "corpus"))
REPORT = os.path.normpath(os.path.join(DIR, "..", "..", "docs", "analysis-report.md"))

# Measured counts: (exact, transposed, ostinato, imitative, curve_points)
CORPUS_PINS = {
    "bach/bwv227.1.mxl": (889, 895, 85, 0, 58),
    "bach/bwv227.3.mxl": (1212, 1215, 171, 0, 59),
    "bach/bwv227.7.mxl": (52, 57, 58, 0, 38),
    "bach/bwv227.11.mxl": (8, 17, 35, 0, 40),
    "byrd/1-Kyrie.mid": (6, 6, 7, 0, 27),
    "byrd/2-Gloria.mid": (36, 72, 195, 0, 299),
    "byrd/3-Credo.mid": (76, 100, 301, 0, 444),
    "byrd/4-Sanctu.mid": (18, 20, 70, 0, 108),
    "byrd/5-Bened.mid": (1, 1, 16, 0, 46),
    "byrd/6-Agnus.mid": (20, 39, 76, 0, 121),
    "schubert/death-and-the-maiden.mxl": (30436, 29401, 9534, 0, 6742),
    "beethoven/beethoven-sym5-mov1.xml": (18763, 16833, 2246, 0, 790),
    "beethoven/beethoven-sym9.xml": (252643, 150243, 14605, 0, 689),
}


def load_corpus(rel):
    return load(os.path.join(CORPUS, rel))


def make_work(notes):
    return Work(parts=[Part(id="P1", name="P1", notes=notes)],
                meta=Meta(source_format="musicxml", ppq=480))


class TestPatternClasses:
    def test_exact_repeats_on_abab(self):
        p = [Note(pitch=60 + (i % 4), onset=i * 240, duration=240) for i in range(8)]
        shifted = [Note(pitch=n.pitch, onset=n.onset + 8 * 240, duration=240) for n in p]
        rep = analyze(make_work(p + shifted), "t")
        assert len(rep.exact) >= 1

    def test_transposed_repeat_detected(self):
        a = [Note(pitch=60 + i, onset=i * 240, duration=240) for i in range(8)]
        b = [Note(pitch=63 + i, onset=1920 + i * 240, duration=240) for i in range(8)]
        rep = analyze(make_work(a + b), "t")
        assert len(rep.transposed) >= 1

    def test_ostinato_on_isochronous_rhythm(self):
        notes = [Note(pitch=60 + (i % 3), onset=i * 240, duration=240) for i in range(20)]
        rep = analyze(make_work(notes), "t")
        assert len(rep.ostinato) >= 1

    def test_delta_curve_nonempty_and_unit_ratios(self):
        notes = [Note(pitch=60, onset=i * 240, duration=240) for i in range(8)]
        rep = analyze(make_work(notes), "t")
        assert len(rep.delta_curve) == 7
        assert all(ratio == 1.0 for _, ratio in rep.delta_curve)

    def test_rests_and_unpitched_excluded_from_points(self):
        notes = [Note(pitch=None, onset=0, duration=480),
                 Note(pitch=None, onset=480, duration=480, notations=frozenset({"unpitched"})),
                 Note(pitch=60, onset=960, duration=480)]
        rep = analyze(make_work(notes), "t")
        assert rep.parts == {"P1": 3}  # report counts all events
        assert len(rep.delta_curve) == 0  # one pitched point → no IOIs


class TestScaleBudget:
    def test_caps_apply_over_2000_points(self):
        pts = [(i * 10, 40 + (i % 24)) for i in range(3000)]
        assert max((len(k) for k in _find_repeats(pts)), default=0) <= 16
        assert max((len(k) for k in _find_transposed(pts)), default=0) <= 12

    def test_small_work_uncapped(self):
        pts = [(i * 240, 60 + (i % 7)) for i in range(300)]
        assert max((len(k) for k in _find_repeats(pts)), default=0) > 16

    @slow
    def test_beethoven9_completes_within_budget(self):
        t0 = time.monotonic()
        rep = analyze(load_corpus("beethoven/beethoven-sym9.xml"), "b9")
        elapsed = time.monotonic() - t0
        assert elapsed < 180  # measured ~32s incl. parse; 5x headroom
        assert len(rep.exact) > 0


class TestCorpusPins:
    @slow
    @pytest.mark.parametrize("rel", sorted(CORPUS_PINS))
    def test_counts_pinned(self, rel):
        exact, transposed, ostinato, imitative, curve = CORPUS_PINS[rel]
        rep = analyze(load_corpus(rel), rel)
        assert len(rep.exact) == exact, rel
        assert len(rep.transposed) == transposed, rel
        assert len(rep.ostinato) == ostinato, rel
        assert len(rep.imitative) == imitative, rel
        assert len(rep.delta_curve) == curve, rel


class TestCLI:
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, CLI, *args],
            capture_output=True, text=True, timeout=900,
            cwd=os.path.join(DIR, ".."),
        )

    def test_per_work_reports_counts(self):
        r = self.run_cli(os.path.join(CORPUS, "bach", "bwv227.1.mxl"))
        assert r.returncode == 0, r.stderr
        assert "exact repeats: 889" in r.stdout
        assert "transposed repeats: 895" in r.stdout
        assert "delta curve points: 58" in r.stdout

    @slow
    def test_all_writes_analysis_report(self):
        r = self.run_cli("--all")
        assert r.returncode == 0, r.stderr
        assert os.path.exists(REPORT)
        text = open(REPORT).read()
        for rel in ("bach/bwv227.1.mxl", "beethoven/beethoven-sym9.xml"):
            assert rel in text
        assert "252643" in text  # B9 exact pin lands in the report
