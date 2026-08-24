"""L2 renderer gap tests (issue #219) — spec:
tests/open_20260824-001141_l2-performance-renderer.md.

Covered here: per-part gain (gap 2), cross-env determinism anchors (gap 4,
in-process byte equality + float64-sensitive recompute), and the
before-first-tempo-tick edge (gap 5).

Deferred per the spec: sfizz/SFZ primary-tier renders (gap 1 — sample
libraries not wired in; the sine-envelope path is the test scope) and
Sonic-level features (gap 3 — belongs to the L4 distiller domain).
"""

import numpy as np

from muse_mockup import Mockup, Note
from muse_render import Renderer, render_to_file


def _read_wav(path):
    import wave
    with wave.open(str(path), "rb") as f:
        return np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16)


def _make_two_part(part_map):
    m = Mockup(work_id="two-part")
    m.notes = [
        Note(pitch=60, onset=0, duration=480, velocity=100, part="P1"),
        Note(pitch=67, onset=0, duration=480, velocity=100, part="P2"),
    ]
    m.tempo_map = [(0, 120000)]
    m.part_map = part_map
    return m


# --- Gap 2: per-part gain ---

def test_part_gain_scales_amplitude(tmp_path):
    """A part with gain 0.5 renders measurably quieter than gain 1.0,
    same pitch/velocity/duration."""
    one = lambda gain: Mockup(
        work_id="g",
        notes=[Note(pitch=60, onset=0, duration=480, velocity=100, part="P1")],
        tempo_map=[(0, 120000)],
        part_map={"P1": {"instrument": "piano", "gain": gain}},
    )
    render_to_file(one(1.0), str(tmp_path / "full.wav"))
    render_to_file(one(0.5), str(tmp_path / "half.wav"))
    full = np.abs(_read_wav(tmp_path / "full.wav")).max()
    half = np.abs(_read_wav(tmp_path / "half.wav")).max()
    assert half < full
    assert half / full > 0.3  # well below full; exact ratio rides normalization


def test_gain_ratio_preserved_when_no_normalization(tmp_path):
    """Below the clip threshold the gain ratio survives linearly: gain 0.5
    is half the amplitude of gain 1.0."""
    one = lambda gain: Mockup(
        work_id="g",
        notes=[Note(pitch=60, onset=0, duration=480, velocity=64, part="P1")],
        tempo_map=[(0, 120000)],
        part_map={"P1": {"gain": gain}},
    )
    render_to_file(one(1.0), str(tmp_path / "a.wav"))
    render_to_file(one(0.5), str(tmp_path / "b.wav"))
    a = np.abs(_read_wav(tmp_path / "a.wav").astype(np.float64)).max()
    b = np.abs(_read_wav(tmp_path / "b.wav").astype(np.float64)).max()
    assert a < 32767  # premise: no normalization kicked in
    assert b / a == np.float64(0.5) or abs(b / a - 0.5) < 0.02


def test_part_map_without_gain_defaults_to_unity(tmp_path):
    """String-valued part_map entries (instrument only) render at gain 1.0 —
    same bytes as an explicit gain: 1.0 dict."""
    string_map = Mockup(
        work_id="t",
        notes=[Note(pitch=60, onset=0, duration=480, velocity=80, part="P1")],
        tempo_map=[(0, 120000)],
        part_map={"P1": "piano"},
    )
    dict_map = Mockup(
        work_id="t",
        notes=[Note(pitch=60, onset=0, duration=480, velocity=80, part="P1")],
        tempo_map=[(0, 120000)],
        part_map={"P1": {"instrument": "piano", "gain": 1.0}},
    )
    render_to_file(string_map, str(tmp_path / "s.wav"))
    render_to_file(dict_map, str(tmp_path / "d.wav"))
    assert (tmp_path / "s.wav").read_bytes() == (tmp_path / "d.wav").read_bytes()


def test_unknown_part_falls_back_to_unity_gain(tmp_path):
    """A note whose part is absent from part_map renders (gain 1.0) rather
    than failing — the renderer is permissive at the seam."""
    m = Mockup(
        work_id="orphan",
        notes=[Note(pitch=60, onset=0, duration=480, velocity=80, part="P9")],
        tempo_map=[(0, 120000)],
        part_map={"P1": "piano"},
    )
    meta = render_to_file(m, str(tmp_path / "o.wav"))
    assert meta["notes"] == 1
    assert np.abs(_read_wav(tmp_path / "o.wav")).max() > 0


# --- Gap 4: determinism anchors ---

def test_fresh_renderer_instance_byte_equal(tmp_path):
    """A new Renderer instance (cold note pool) produces identical bytes —
    the no-hidden-process-state anchor for cross-environment determinism."""
    m = _make_two_part({"P1": {"gain": 1.0}, "P2": {"gain": 0.7}})
    Renderer().render_mockup(m, str(tmp_path / "a.wav"))
    Renderer().render_mockup(m, str(tmp_path / "b.wav"))
    assert (tmp_path / "a.wav").read_bytes() == (tmp_path / "b.wav").read_bytes()


def test_render_is_pure_with_respect_to_input(tmp_path):
    """Rendering must not mutate the mockup — re-rendering the same object
    after inspection gives identical bytes (guards against in-place
    normalization bugs breaking golden anchors)."""
    m = _make_two_part({"P1": {"gain": 1.0}, "P2": {"gain": 0.7}})
    notes_before = [(n.pitch, n.onset, n.duration, n.velocity, n.part) for n in m.notes]
    render_to_file(m, str(tmp_path / "a.wav"))
    notes_after = [(n.pitch, n.onset, n.duration, n.velocity, n.part) for n in m.notes]
    assert notes_before == notes_after
    render_to_file(m, str(tmp_path / "b.wav"))
    assert (tmp_path / "a.wav").read_bytes() == (tmp_path / "b.wav").read_bytes()


# --- Gap 5: before-first-tempo-tick edge ---

def test_onset_before_first_tempo_tick_uses_default_120bpm():
    """Notes with onset ahead of the first tempo-map tick inherit 120 bpm
    (the pinned predictable preference, not a failure)."""
    r = Renderer()
    # First tempo event at tick 960; onset at 480 is before it.
    tempo_map = [(960, 240000)]  # 240 bpm from tick 960 on
    got = r.ticks_to_sec(480, tempo_map)
    expect_120 = 480 * 60.0 / (120 * 480)  # 0.5s at default 120 bpm
    assert got == expect_120


def test_tempo_edge_note_renders_at_default_position(tmp_path):
    """End-to-end pin of the same edge: a note starting at tick 480 with the
    map's first event at 960 lands its peak at the 120-bpm position."""
    m = Mockup(
        work_id="edge",
        notes=[Note(pitch=60, onset=480, duration=480, velocity=100, part="P1")],
        tempo_map=[(960, 240000)],
        part_map={"P1": "piano"},
    )
    meta = render_to_file(m, str(tmp_path / "e.wav"))
    data = _read_wav(tmp_path / "e.wav")
    onset_sample = int(0.5 * 44100)  # 0.5s at default 120 bpm
    window = np.abs(data[onset_sample:onset_sample + 4410])
    assert window.max() > 1000  # audible energy at the 120-bpm position
    assert np.abs(data[: int(0.4 * 44100)]).max() == 0  # silence before it


def test_empty_tempo_map_falls_back_to_120bpm():
    r = Renderer()
    assert r.ticks_to_sec(480, []) == 0.5
    assert r.ticks_to_sec(480, None) == 0.5
