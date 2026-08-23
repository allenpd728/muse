"""Tests: W5 visualizer (issue #134).

Spec: tests/open_20260823-192000_w5-visualizer.md — rendering, robustness,
output contract.
"""

import os
import subprocess
import sys

import pytest

from muse_ir import load
from muse_ir.model import Meta, Note, Part, Work
from muse_viz import PianoRollConfig, build_title, pitch_value, render

DIR = os.path.dirname(__file__)
CLI = os.path.join(DIR, "cli.py")
CORPUS = os.path.normpath(os.path.join(DIR, "..", "..", "corpus"))

BACH1 = os.path.join(CORPUS, "bach", "bwv227.1.mxl")
KYRIE = os.path.join(CORPUS, "byrd", "1-Kyrie.mid")
B9 = os.path.join(CORPUS, "beethoven", "beethoven-sym9.xml")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def assert_png(path):
    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read(8) == PNG_MAGIC
    assert os.path.getsize(path) > 1000  # a real plot, not an empty frame


class TestRendering:
    def test_bach_chorale_renders(self, tmp_path):
        work = load(BACH1)
        out = str(tmp_path / "chorale.png")
        res = render(work, PianoRollConfig(out=out))
        assert_png(out)
        assert res.parts_rendered == [p.id for p in work.parts]
        assert res.events == 279

    def test_byrd_kyrie_midi_path_renders(self, tmp_path):
        work = load(KYRIE)
        out = str(tmp_path / "byrd.png")
        res = render(work, PianoRollConfig(out=out))
        assert_png(out)
        assert len(res.parts_rendered) == 3
        assert res.events == 71

    def test_beethoven9_subset_renders(self, tmp_path):
        work = load(B9)
        ids = [p.id for p in work.parts[:8]]
        out = str(tmp_path / "b9.png")
        res = render(work, PianoRollConfig(parts=ids, out=out))
        assert_png(out)
        assert res.parts_rendered == ids


class TestRobustness:
    def test_none_pitch_rest_maps_to_sentinel(self):
        assert pitch_value(Note(pitch=None, onset=0, duration=480)) == -1

    def test_unpitched_maps_distinctly(self):
        n = Note(pitch=None, onset=0, duration=480, notations=frozenset({"unpitched"}))
        assert pitch_value(n) == -2

    def test_zero_duration_notes_render(self, tmp_path):
        work = Work(
            parts=[Part(id="P1", name="P1", notes=[
                Note(pitch=60, onset=0, duration=0),   # grace-like
                Note(pitch=64, onset=480, duration=480),
            ])],
            meta=Meta(source_format="musicxml", ppq=480),
        )
        out = str(tmp_path / "grace.png")
        res = render(work, PianoRollConfig(out=out))
        assert_png(out)
        assert res.events == 2

    def test_part_subset_renders_only_those_lanes(self, tmp_path):
        work = load(BACH1)
        ids = [p.id for p in work.parts[:2]]
        out = str(tmp_path / "subset.png")
        res = render(work, PianoRollConfig(parts=ids, out=out))
        assert res.parts_rendered == ids
        assert res.events == sum(len(p.notes) for p in work.parts[:2])

    def test_unknown_part_id_skipped_not_crash(self, tmp_path):
        work = load(BACH1)
        out = str(tmp_path / "bogus.png")
        res = render(work, PianoRollConfig(parts=["NOPE", work.parts[0].id], out=out))
        assert res.parts_rendered == [work.parts[0].id]


class TestOutput:
    def test_title_includes_part_and_event_counts(self):
        work = load(BACH1)
        title = build_title(work, [p.id for p in work.parts], work.note_count)
        assert "4 parts" in title
        assert "279 events" in title

    def test_cli_renders_bach(self, tmp_path):
        out = str(tmp_path / "cli.png")
        r = subprocess.run(
            [sys.executable, CLI, BACH1, "--out", out],
            capture_output=True, text=True, timeout=600,
            cwd=os.path.join(DIR, ".."),
        )
        assert r.returncode == 0, r.stderr
        assert "rendered 4 parts" in r.stdout
        assert_png(out)

    def test_cli_first_flag_selects_subset(self, tmp_path):
        out = str(tmp_path / "cli2.png")
        r = subprocess.run(
            [sys.executable, CLI, KYRIE, "--first", "2", "--out", out],
            capture_output=True, text=True, timeout=600,
            cwd=os.path.join(DIR, ".."),
        )
        assert r.returncode == 0, r.stderr
        assert "rendered 2 parts" in r.stdout
        assert_png(out)
