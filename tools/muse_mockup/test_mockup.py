"""Tests: L1 mockup harness (#180). Spec: tests/open_20260823-235000_l1-mockup.md."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from muse_ir import load  # noqa: E402
from muse_mockup import Mockup, Note, add_note, validate_mockup, dump_mockup, load_mockup, MockupError  # noqa: E402
from muse_seed import Seed  # noqa: E402
from muse_seed_cli.cli import _validate  # noqa: E402

CORPUS = os.path.join(os.path.dirname(__file__), "..", "..", "corpus")


def _load(work_rel):
    return load(os.path.join(CORPUS, work_rel))


def _make_mockup(work_rel, work_id="test"):
    w = _load(work_rel)
    m = Mockup(work_id=work_id)
    for p in w.parts:
        for n in p.notes:
            if n.pitch is None or getattr(n, "is_rest", False) or getattr(n, "is_unpitched", False):
                continue
            add_note(m, Note(pitch=n.pitch, onset=n.onset, duration=n.duration, velocity=64, part=p.id))
    return m


def _pitched_count(work_rel):
    w = _load(work_rel)
    return sum(sum(1 for n in p.notes if n.pitch is not None
                   and not getattr(n, "is_rest", False) and not getattr(n, "is_unpitched", False))
                   for p in w.parts)


class TestModelValidation:
    def test_empty_mockup_raises(self):
        with pytest.raises(MockupError, match="empty mockup"):
            Mockup(work_id="x").validate()

    def test_valid_mockup_passes(self):
        m = Mockup(work_id="x")
        add_note(m, Note(pitch=64, onset=0, duration=480, velocity=64, part="P1"))
        m.validate()

    def test_negative_offset_rejected(self):
        m = Mockup(work_id="x")
        add_note(m, Note(pitch=64, onset=0, duration=480, velocity=64,
                         attack_ms=-0.1, part="P1"))
        with pytest.raises(MockupError, match="negative offset"):
            m.validate()


class TestDumpLoad:
    def test_roundtrip_json(self):
        m = Mockup(work_id="x")
        add_note(m, Note(pitch=64, onset=0, duration=480, velocity=72,
                         onset_offset_ms=17.5, attack_ms=10.0, release_ms=20.0,
                         swell=-0.5, part="P1"))
        y = dump_mockup(m, fmt="json")
        m2 = load_mockup(y, fmt="json")
        assert m2.notes[0].pitch == 64
        assert m2.notes[0].onset_offset_ms == 17.5
        assert m2.notes[0].swell == -0.5

    def test_roundtrip_yaml(self):
        m = Mockup(work_id="x")
        add_note(m, Note(pitch=64, onset=0, duration=480, velocity=72,
                         onset_offset_ms=17.5, attack_ms=10.0, release_ms=20.0,
                         swell=-0.5, part="P1"))
        y = dump_mockup(m, fmt="yaml")
        m2 = load_mockup(y, fmt="yaml")
        assert m2.notes[0].pitch == 64


class TestCorpusAndCLI:
    @pytest.mark.parametrize("rel,expected", [
        ("bach/bwv227.1.mxl", 279),
        ("byrd/1-Kyrie.mid", 71),
        ("schubert/death-and-the-maiden.mxl", 22869),
    ])
    def test_note_count_matches_pitched(self, rel, expected):
        m = _make_mockup(rel)
        assert len(m.notes) == expected
        assert _pitched_count(rel) == expected

    def test_cli_exit_zero(self, tmp_path, monkeypatch):
        out = tmp_path / "t.json"
        monkeypatch.setattr(sys, "argv", ["cli.py", f"{CORPUS}/bach/bwv227.1.mxl", "--out", str(out)])
        from muse_mockup.cli import main
        rc = main()
        assert rc == 0
        assert out.exists()


class TestValidationWithAssertions:
    def test_register_bounds(self):
        m = Mockup(work_id="x")
        add_note(m, Note(pitch=64, onset=0, duration=480, velocity=64, part="P4"))
        # C3..C5 encompasses pitch 64 (E4)
        validate_mockup(m, {"assertions": {"register": {"part": "P4", "min": "C3", "max": "C5"}}})

    def test_register_violation_fails(self):
        from muse_assert import AssertionError
        m = Mockup(work_id="x")
        add_note(m, Note(pitch=64, onset=0, duration=480, velocity=64, part="P4"))
        with pytest.raises(AssertionError):
            validate_mockup(m, {"assertions": {"register": {"part": "P4", "min": "C5", "max": "C7"}}})


class TestCorpusIntegration:
    @pytest.mark.parametrize("rel", ["bach/bwv227.1.mxl", "byrd/1-Kyrie.mid"])
    def test_end_to_end_validate_with_seed(self, tmp_path, rel):
        m = _make_mockup(rel)
        seed = Seed(
            format_version="0.1",
            work_id="t",
            params={"tempo": {"min_bpm": 60, "max_bpm": 130, "default_bpm": 96}},
            philosophy={"tempo_philosophy": ["flexible"], "dynamic_philosophy": ["terraced"],
                         "provenance": {"author": "t", "ai_assisted": False}},
            variation_points=[],
            assertions={"register": {"part": "P1", "min": "C1", "max": "C8"}},
            provenance={"source": "t"},
        )
        path = tmp_path / "s.yaml"
        from muse_seed import dump_seed
        path.write_text(dump_seed(seed, fmt="yaml"))
        rc = _validate(str(path), f"{CORPUS}/{rel}")
        assert rc == 0
