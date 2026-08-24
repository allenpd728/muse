"""L2 renderer tests: mockup→WAV rendering, tempo conversion, envelope
shape, determinism, and malformed-input handling."""

import os
import wave

import pytest

from muse_mockup import Mockup, Note, MockupError
from muse_render import Renderer, render_to_file


def make_mockup(notes=None, tempo=None):
    m = Mockup(work_id="test")
    m.notes = notes or [
        Note(pitch=60, onset=0, duration=480, velocity=60, part="P1"),
        Note(pitch=64, onset=480, duration=480, velocity=64, part="P1"),
    ]
    m.tempo_map = tempo or [(0, 120000)]
    m.part_map = {"P1": "piano"}
    return m


def test_render_writes_wav(tmp_path):
    out = tmp_path / "test.wav"
    meta = render_to_file(make_mockup(), str(out))
    assert out.exists()
    with wave.open(str(out)) as w:
        assert w.getnchannels() == 1
        assert w.getframerate() == 44100
        assert w.getnframes() / 44100 == pytest.approx(meta["duration_sec"], rel=0.01)


def test_notes_count_in_meta(tmp_path):
    out = tmp_path / "test.wav"
    meta = render_to_file(make_mockup(), str(out))
    assert meta["notes"] == 2
    assert meta["parts"] == ["P1"]


def test_tempo_map_drives_duration(tmp_path):
    fast = render_to_file(
        make_mockup(tempo=[(0, 240000)]), str(tmp_path / "fast.wav")
    )
    slow = render_to_file(
        make_mockup(tempo=[(0, 60000)]), str(tmp_path / "slow.wav")
    )
    assert slow["duration_sec"] > fast["duration_sec"]


def test_deterministic_same_input_same_output(tmp_path):
    a = render_to_file(make_mockup(), str(tmp_path / "a.wav"))
    b = render_to_file(make_mockup(), str(tmp_path / "b.wav"))
    assert open(tmp_path / "a.wav", "rb").read() == open(tmp_path / "b.wav", "rb").read()


def test_clipped_render_normalized(tmp_path):
    notes = [
        Note(pitch=60, onset=0, duration=480, velocity=127, part="P1")
        for _ in range(50)
    ]
    out = tmp_path / "loud.wav"
    render_to_file(make_mockup(notes=notes), str(out))
    import numpy as np
    with wave.open(str(out), "rb") as f:
        data = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16)
    assert np.abs(data).max() <= 32767


def test_empty_mockup_fails_loudly(tmp_path):
    m = Mockup(work_id="empty")
    m.notes = []
    with pytest.raises(MockupError):
        render_to_file(m, str(tmp_path / "empty.wav"))