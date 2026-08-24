"""ppq regression tests (bug #246): the tick domain rides the Mockup.

Before the fix, ticks_to_sec defaulted to ppq=480 and render_mockup never
overrode it — every render of a real corpus work played at the wrong
speed (bwv227.1, ppq=2, rendered 240× too fast: 0.69s instead of ~47s).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_ir import load  # noqa: E402
from muse_mockup import Mockup, Note  # noqa: E402
from muse_render import Renderer, render_to_file  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _mockup(ppq, last_tick):
    m = Mockup(work_id="ppq", ppq=ppq)
    m.notes = [Note(pitch=60, onset=0, duration=last_tick, velocity=80, part="P1")]
    m.tempo_map = [(0, 120000)]
    m.part_map = {"P1": "piano"}
    return m


def test_ppq2_domain_renders_at_real_speed(tmp_path):
    """152 ticks at ppq=2 → 76 quarter notes → 38s at 120bpm (+0.5 tail).
    The exact bwv227.1 tick domain from the bug report."""
    meta = render_to_file(_mockup(ppq=2, last_tick=152), str(tmp_path / "m.wav"))
    assert meta["duration_sec"] == pytest.approx(38.5, rel=0.01)


def test_ppq192_domain_renders_at_real_speed(tmp_path):
    """12288 ticks at ppq=192 → 64 quarters → 32s at 120bpm (+0.5 tail).
    The Byrd MIDI tick domain."""
    meta = render_to_file(_mockup(ppq=192, last_tick=12288), str(tmp_path / "b.wav"))
    assert meta["duration_sec"] == pytest.approx(32.5, rel=0.01)


def test_default_ppq_unchanged(tmp_path):
    """Mockups without ppq keep the 480 default — existing artifacts and
    tests are unaffected (additive field)."""
    m = _mockup(ppq=480, last_tick=960)
    m.ppq = 480  # explicit default, same as an old mockup that never set it
    meta = render_to_file(m, str(tmp_path / "d.wav"))
    assert meta["duration_sec"] == pytest.approx(1.5, rel=0.01)


def test_ppq_round_trips_through_serialization():
    from muse_mockup import dump_mockup, load_mockup
    m = _mockup(ppq=2, last_tick=4)
    assert load_mockup(dump_mockup(m)).ppq == 2
    # and the default stays implicit — no ppq key emitted for 480
    default = _mockup(ppq=480, last_tick=4)
    assert '"ppq":' not in dump_mockup(default)
    assert load_mockup(dump_mockup(default)).ppq == 480


def test_real_work_tick_domain_matches_meta_ppq():
    """Pin the premise: the corpus works' own ppq values (the numbers the
    bug report cites) are what the IR reports."""
    bach = load(os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl"))
    byrd = load(os.path.join(REPO, "corpus", "byrd", "1-Kyrie.mid"))
    assert bach.meta.ppq == 2
    assert bach.duration_ticks() == 152
    assert byrd.meta.ppq == 192


def test_bwv227_scale_render_is_plausible(tmp_path):
    """A bwv227.1-shaped mockup (real duration domain, seed-ish tempo)
    renders in the 45–75s band the DoD pins — not 0.69s."""
    m = Mockup(work_id="bwv227.1", ppq=2)
    m.notes = [Note(pitch=60, onset=0, duration=152, velocity=70, part="P1")]
    m.tempo_map = [(0, 100000)]  # seed tempo ~100 bpm
    m.part_map = {"P1": "piano"}
    meta = render_to_file(m, str(tmp_path / "w.wav"))
    assert 45 <= meta["duration_sec"] <= 75
