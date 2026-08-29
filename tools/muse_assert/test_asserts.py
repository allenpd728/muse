"""Tests: S3.5 assertions (issue #158).

Spec: tests/open_20260823-213000_s3-assertions.md — assertion kinds,
fail-loud behavior.
"""

import os

import pytest

from muse_assert import AssertionError, validate_assertions
from muse_ir import load
from muse_ir.model import Maps, Meta, Note, Part, Work

CORPUS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "corpus"))
BACH1 = os.path.join(CORPUS, "bach", "bwv227.1.mxl")


@pytest.fixture(scope="module")
def bach():
    return load(BACH1)


def make_work(notes, tempo=None):
    return Work(
        parts=[Part(id="P1", name="P1", notes=notes)],
        maps=Maps(tempo=tempo or []),
        meta=Meta(source_format="musicxml", ppq=480),
    )


class TestMustContain:
    def test_theme_present_passes(self, bach):
        validate_assertions(bach, {"must_contain": [[71, 73, 74]]})  # B4 C#5 D5

    def test_theme_absent_fails(self, bach):
        with pytest.raises(AssertionError, match="must_contain"):
            validate_assertions(bach, {"must_contain": [[71, 72, 74]]})

    def test_failure_names_theme(self, bach):
        try:
            validate_assertions(bach, {"must_contain": [[1, 2, 3]]})
            pytest.fail("expected AssertionError")
        except AssertionError as e:
            assert "[1, 2, 3]" in str(e)
            assert e.kind == "must_contain"

    def test_theme_across_parts(self):
        # theme must be found within a single part's pitch sequence
        w = Work(parts=[
            Part(id="A", name="A", notes=[Note(pitch=60, onset=0, duration=480),
                                          Note(pitch=62, onset=480, duration=480)]),
            Part(id="B", name="B", notes=[Note(pitch=64, onset=0, duration=480)]),
        ], meta=Meta(source_format="musicxml", ppq=480))
        validate_assertions(w, {"must_contain": [[60, 62]]})
        with pytest.raises(AssertionError):
            validate_assertions(w, {"must_contain": [[60, 64]]})  # spans parts


class TestRegister:
    def test_within_bounds_passes(self, bach):
        validate_assertions(bach, {"register": {"part": "P4", "min": "C2", "max": "C4"}})

    def test_violation_fails_naming_part_and_pitch(self, bach):
        with pytest.raises(AssertionError, match=r"\[register\]"):
            validate_assertions(bach, {"register": {"part": "P4", "min": "C2", "max": "A3"}})

    def test_note_name_parsing(self):
        from muse_assert.asserts import _note_name_to_pitch, _pitch_to_note_name
        assert _note_name_to_pitch("C4") == 60
        assert _note_name_to_pitch("A4") == 69
        assert _note_name_to_pitch("C#3") == 49
        assert _pitch_to_note_name(60) == "C4"
        assert _pitch_to_note_name(69) == "A4"

    def test_rests_and_unpitched_ignored(self):
        w = make_work([Note(pitch=None, onset=0, duration=480),
                       Note(pitch=None, onset=480, duration=480, notations=frozenset({"unpitched"})),
                       Note(pitch=60, onset=960, duration=480)])
        validate_assertions(w, {"register": {"part": "P1", "min": "C4", "max": "C4"}})

    def test_part_selector_by_name(self, bach):
        part_name = bach.parts[3].name
        validate_assertions(bach, {"register": {"part": part_name, "min": "C2", "max": "C4"}})


class TestForm:
    def test_empty_sections_tolerant(self, bach):
        validate_assertions(bach, {"form": {"sections": []}})

    def test_notation_backed_section_found(self):
        w = make_work([Note(pitch=60, onset=0, duration=480, notations=frozenset({"A"}))])
        validate_assertions(w, {"form": {"sections": ["A"]}})

    def test_missing_section_fails(self):
        w = make_work([Note(pitch=60, onset=0, duration=480)])
        with pytest.raises(AssertionError, match="missing sections"):
            validate_assertions(w, {"form": {"sections": ["B"]}})


class TestTempoBounds:
    def test_within_bounds_passes(self, bach):
        validate_assertions(bach, {"tempo_bounds": {"min_bpm": 60, "max_bpm": 130}})

    def test_below_min_fails(self):
        w = make_work([Note(pitch=60, onset=0, duration=480)], tempo=[(0, 50000)])
        with pytest.raises(AssertionError, match="tempo 50.0 < 60"):
            validate_assertions(w, {"tempo_bounds": {"min_bpm": 60}})

    def test_above_max_fails(self):
        w = make_work([Note(pitch=60, onset=0, duration=480)], tempo=[(0, 200000)])
        with pytest.raises(AssertionError, match="tempo 200.0 > 130"):
            validate_assertions(w, {"tempo_bounds": {"max_bpm": 130}})


class TestFailLoud:
    def test_unknown_kind_rejected(self, bach):
        with pytest.raises(AssertionError, match="unknown-assertion-kind"):
            validate_assertions(bach, {"vibe_check": True})

    def test_empty_assertions_noop(self, bach):
        validate_assertions(bach, {})
        validate_assertions(bach, None)

    def test_error_carries_kind(self, bach):
        try:
            validate_assertions(bach, {"register": {"part": "P4", "min": "C2", "max": "A3"}})
            pytest.fail("expected AssertionError")
        except AssertionError as e:
            assert e.kind == "register"


class TestFormCurveCorrelation:

    def _curve_work(self):
        """Deterministic AAAAAAAA curve: isochronous repeated monophonic C4."""
        notes = [Note(pitch=60, onset=i * 480, duration=480) for i in range(16)]
        return make_work(notes)

    def test_run_present_passes(self):
        w = self._curve_work()
        validate_assertions(w, {"form_curve_correlation": {"letters": ["A", "A"]}})
        validate_assertions(w, {"form_curve_correlation": {"letters": ["A"] * 8}})

    def test_run_absent_fails(self):
        w = self._curve_work()
        with pytest.raises(AssertionError, match="form_curve_correlation"):
            validate_assertions(w, {"form_curve_correlation": {"letters": ["B", "B"]}})

    def test_failure_names_derived_curve(self):
        w = self._curve_work()
        try:
            validate_assertions(w, {"form_curve_correlation": {"letters": ["Z"]}})
            pytest.fail("expected AssertionError")
        except AssertionError as e:
            assert e.kind == "form_curve_correlation"

    def test_empty_letters_noop(self):
        validate_assertions(self._curve_work(), {"form_curve_correlation": {"letters": []}})

    def test_window_beats_override_accepted(self):
        w = self._curve_work()
        validate_assertions(w, {"form_curve_correlation": {"letters": ["A"], "window_beats": 1}})
