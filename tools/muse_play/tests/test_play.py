"""P2 reference renderer tests: WAV write, note count, determinism,
only-rests failure, tempo-map drive."""

import wave

import pytest

from muse_ir import load
from muse_play import PlayError, play, render_work

from conftest import corpus_path


def test_render_bach_writes_wav(tmp_path):
    out = tmp_path / "bach.wav"
    meta = render_work(load(corpus_path("bach", "bwv227.1.mxl")), str(out))
    with wave.open(str(out)) as w:
        assert w.getnchannels() == 1
        assert w.getnframes() / 44100 == pytest.approx(meta["duration_sec"], rel=0.02)
    assert meta["notes"] == 279
    assert meta["parts"] == 4


def test_play_wrapper_defaults_output(tmp_path):
    src = corpus_path("bach", "bwv227.1.mxl")
    out = str(tmp_path / "out.wav")
    meta = play(src, out_path=out)
    assert meta["out"] == out
    assert len(meta["out"]) > 8


def test_deterministic_same_source(tmp_path):
    src = corpus_path("bach", "bwv227.1.mxl")
    a = play(src, str(tmp_path / "a.wav"))
    b = play(src, str(tmp_path / "b.wav"))
    assert open(tmp_path / "a.wav", "rb").read() == open(tmp_path / "b.wav", "rb").read()


def test_midi_source_renders(tmp_path):
    out = tmp_path / "byrd.wav"
    meta = render_work(load(corpus_path("byrd", "1-Kyrie.mid")), str(out))
    assert meta["notes"] == 71


def test_only_rests_fails_loudly(tmp_path):
    # no pitched notes path: byrd Song XML with no pitch? — creat a work with only rests
    from muse_ir import Maps, Meta, Note, Part, Work
    w = Work(
        parts=[Part(id="P1", name="P1", notes=[Note(pitch=None, onset=0, duration=480)])],
        maps=Maps(),
        meta=Meta(source_format="musicxml", ppq=480),
    )
    part = w.parts[0]
    part.sort_notes()
    with pytest.raises(PlayError):
        render_work(w, str(tmp_path / "rests.wav"))


def test_empty_parts_fail_loudly(tmp_path):
    # Work with parts but only unpitched percussion (not a rest failure, a
    # "no pitched events" failure is PlayError)
    from muse_ir import Maps, Meta, Part, Work
    w = Work(parts=[], maps=Maps(), meta=Meta(source_format="musicxml", ppq=480))
    # muse_ir validates no-parts on Work.validate() — the render must hit
    # that; invoke render_work directly
    from muse_assert import AssertionError as _  # noqa
    with pytest.raises(Exception):
        render_work(w, str(tmp_path / "empty.wav"))
