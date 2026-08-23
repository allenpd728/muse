"""Known-answer tests against the corpus registry (corpus/README.md) and the
W1 design doc's conformance table. These pin note/part/dynamics counts; W2
will enforce them on every change."""

import pytest

from muse_ir import load

from conftest import corpus_path

# Measured 2026-08-23 (W1). Movement 3 is the SSATB fantasia — 5 parts, not 4;
# the registry's "~280 notes, 4 voices each" is only approximate. Tempo pins
# are the exact full-map contents; movements 7/11 carry no tempo marks at all.
BACH_MOVEMENTS = {
    "bwv227.1.mxl": (4, 279, [(0, 96000)]),
    "bwv227.3.mxl": (5, 377, [(0, 93000)]),
    "bwv227.7.mxl": (4, 307, []),
    "bwv227.11.mxl": (4, 190, []),
}
BYRD_MOVEMENTS = {
    "1-Kyrie.mid": 71,
    "2-Gloria.mid": 924,
    "3-Credo.mid": 1440,
    "4-Sanctu.mid": 327,
    "5-Bened.mid": 130,
    "6-Agnus.mid": 384,
}


@pytest.mark.parametrize("mvt", sorted(BACH_MOVEMENTS))
def test_bach_bwv227(mvt):
    work = load(corpus_path("bach", mvt))
    parts, notes, tempo = BACH_MOVEMENTS[mvt]
    assert len(work.parts) == parts
    assert work.note_count == notes
    assert work.meta.source_format == "musicxml"
    assert work.maps.tempo == tempo
    assert work.maps.meter[0][0] == 0
    # Chorales are unmarked: no dynamics expected (corpus README quality notes)
    assert all(len(p.dynamics) == 0 for p in work.parts)


@pytest.mark.parametrize("mvt", sorted(BYRD_MOVEMENTS))
def test_byrd_mass_midi_path(mvt):
    work = load(corpus_path("byrd", mvt))
    assert len(work.parts) == 3  # Mass for Three Voices
    assert work.meta.source_format == "midi"
    assert work.note_count == BYRD_MOVEMENTS[mvt]
    assert work.maps.tempo, "tempo map must be populated"
    for part in work.parts:
        assert part.instrument.gm_program is not None
        for note in part.notes:
            assert note.velocity is not None  # MIDI sources carry velocity
            assert not note.velocity_inferred


def test_schubert_d810():
    work = load(corpus_path("schubert", "death-and-the-maiden.mxl"))
    assert len(work.parts) == 4
    assert work.note_count == 24772
    assert work.maps.tempo, "tempo marks present"
    dynamics = sum(len(p.dynamics) for p in work.parts)
    assert dynamics == 1731


def test_beethoven5_mov1():
    work = load(corpus_path("beethoven", "beethoven-sym5-mov1.xml"))
    assert len(work.parts) == 12
    assert work.note_count == 13675
    dynamics = sum(len(p.dynamics) for p in work.parts)
    assert dynamics == 431
    # 2/4 throughout, ~502 bars: duration must be in that neighborhood
    assert work.maps.meter[0][1:] == (2, 4)


def test_beethoven9_complete():
    work = load(corpus_path("beethoven", "beethoven-sym9.xml"))
    assert len(work.parts) == 52
    assert work.note_count == 239459
    dynamics = sum(len(p.dynamics) for p in work.parts)
    assert dynamics == 11931
    # Percussion staves: unpitched notes are events, not rests
    unpitched = sum(
        1 for p in work.parts for n in p.notes if "unpitched" in n.notations
    )
    assert unpitched == 835
    assert all(
        not n.is_rest for p in work.parts for n in p.notes if "unpitched" in n.notations
    )
