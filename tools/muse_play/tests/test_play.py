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


def test_sub_sample_note_renders(tmp_path):
    """A note whose duration rounds to <1 audio sample (fast tempo, 1-tick
    duration) must not crash the envelope (regression: env[-0:] broadcast)."""
    from muse_ir import Maps, Meta, Note, Part, Work
    w = Work(
        parts=[Part(id="P1", name="P1", notes=[
            Note(pitch=69, onset=0, duration=1),          # sub-sample at high tempo
            Note(pitch=72, onset=480, duration=480),
        ])],
        maps=Maps(tempo=[(0, 240000)]),                   # 240 bpm
        meta=Meta(source_format="musicxml", ppq=480),
    )
    w.parts[0].sort_notes()
    meta = render_work(w, str(tmp_path / "short.wav"))
    assert meta["notes"] == 2
    assert meta["duration_sec"] > 0


# --- .mu container input (issue #225, spec gap 1): the CLI's format list
# now matches P1's acceptance — containers decode via muse_decode.

import os
import subprocess
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TOOLS = os.path.join(REPO, "tools")
VECTOR = os.path.join(TOOLS, "muse_ci", "vectors", "bach-bwv227.1.mu")


def test_cli_mu_container_renders(tmp_path):
    """P3's golden vector renders through the CLI end-to-end."""
    assert os.path.exists(VECTOR), "P3 vector store must exist"
    out = tmp_path / "vec.wav"
    proc = subprocess.run(
        [sys.executable, "-m", "muse_play", VECTOR, "-o", str(out)],
        cwd=TOOLS, capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "279 notes" in proc.stdout
    assert "4 parts" in proc.stdout
    with wave.open(str(out)) as w:
        assert w.getnframes() > 44100


def test_mu_matches_source_render(tmp_path):
    """The .mu container and its corpus source decode to the same render
    bytes — the S1 contract through two input paths."""
    sys.path.insert(0, os.path.join(TOOLS, "muse_decode"))
    sys.path.insert(0, os.path.join(TOOLS, "muse_mu"))
    sys.path.insert(0, os.path.join(TOOLS, "muse_roll"))
    from muse_decode import decode

    a = render_work(decode(VECTOR), str(tmp_path / "from_mu.wav"))
    b = render_work(load(corpus_path("bach", "bwv227.1.mxl")),
                    str(tmp_path / "from_src.wav"))
    assert a["notes"] == b["notes"] == 279
    assert open(tmp_path / "from_mu.wav", "rb").read() == \
        open(tmp_path / "from_src.wav", "rb").read()


def test_cli_unsupported_format_still_loud(tmp_path):
    """Truly unsupported suffixes keep the loud exit-2 contract."""
    bogus = tmp_path / "nope.txt"
    bogus.write_text("not music")
    proc = subprocess.run(
        [sys.executable, "-m", "muse_play", str(bogus)],
        cwd=TOOLS, capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 2
    assert "unsupported" in proc.stderr.lower()
