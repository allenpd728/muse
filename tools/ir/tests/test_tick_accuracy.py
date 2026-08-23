"""Golden-vector tests: pin *positions*, not just counts (spec gap 1).

Counts can survive a parser regression that shifts every onset by one tick;
these vectors cannot. Each entry was extracted from the corpus source at
commit time and is a load-bearing pin for W4's diff tool.
"""

from conftest import corpus_path

from muse_ir import load


def tuples(work, part_id):
    part = next(p for p in work.parts if p.id == part_id)
    return [(n.pitch, n.onset, n.duration, n.voice) for n in part.notes]


def test_bach_bwv227_1_positions():
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    assert work.duration_ticks() == 152
    golden = {
        "P1": [(71, 0, 2, 1), (75, 76, 4, 1), (64, 144, 8, 1)],
        "P2": [(67, 0, 2, 1), (62, 70, 2, 1), (59, 144, 8, 1)],
        "P3": [(64, 0, 2, 1), (55, 70, 1, 1), (56, 144, 8, 1)],
        "P4": [(52, 0, 2, 1), (52, 72, 1, 1), (52, 144, 8, 1)],
    }
    for part_id, (first, mid, last) in golden.items():
        notes = tuples(work, part_id)
        assert notes[0] == first, part_id
        assert notes[len(notes) // 2] == mid, part_id
        assert notes[-1] == last, part_id


def test_byrd_kyrie_positions():
    work = load(corpus_path("byrd", "1-Kyrie.mid"))
    assert work.duration_ticks() == 12288
    golden = {
        "track2": (67, 0, 1152, 1, 60),
        "track3": (58, 0, 1152, 1, 60),
        "track4": (51, 0, 1152, 1, 60),
    }
    for part_id, first in golden.items():
        part = next(p for p in work.parts if p.id == part_id)
        n = part.notes[0]
        assert (n.pitch, n.onset, n.duration, n.voice, n.velocity) == first


def test_beethoven5_duration_and_vocab():
    work = load(corpus_path("beethoven", "beethoven-sym5-mov1.xml"))
    assert work.duration_ticks() == 2008
    assert work.meta.ppq == 2
    flute = next(p for p in work.parts if p.id == "P1")
    first = flute.notes[0]
    assert first.pitch is None and first.onset == 0 and first.duration == 4
    # Per-part key signatures (transposing instruments) all anchor at tick 0.
    assert sorted(work.maps.key) == [
        (0, -3, "minor"),
        (0, -1, "minor"),
        (0, 0, "major"),
    ]
    assert [d.text for d in flute.dynamics[:3]] == ["p", "mp", "mf"]


def test_grace_note_onset_semantics():
    """Gap 2: grace notes share the following note's cursor. Pin the first
    grace passage in Schubert Violin 1 (tick 79080): grace E5 at duration 0
    sandwiched between A4 (49080+90) and D5."""
    work = load(corpus_path("schubert", "death-and-the-maiden.mxl"))
    violin = next(p for p in work.parts if p.id == "P1")
    graces = [n for n in violin.notes if "grace" in n.notations]
    assert len(graces) >= 1
    first_grace = graces[0]
    idx = violin.notes.index(first_grace)
    prev, nxt = violin.notes[idx - 1], violin.notes[idx + 1]
    assert first_grace.pitch == 69 and first_grace.duration == 0
    assert prev.pitch == 67 and prev.onset == 79080 and prev.duration == 90
    assert nxt.pitch == 66 and nxt.onset == 79170 and nxt.duration == 30
    # The grace note's onset must not precede the sounding note it ornaments.
    assert first_grace.onset >= prev.onset


def test_lossiness_is_pinned():
    """Gap 4: numbered slur/tie concurrency collapses to flags by design.
    Beethoven 5 has notes under multiple concurrent slurs; the IR keeps only
    membership flags. This test makes the deliberate lossiness visible:
    slur-start and slur-stop flags exist, counts needn't balance, and no
    numbering survives."""
    work = load(corpus_path("beethoven", "beethoven-sym5-mov1.xml"))
    starts = stops = 0
    for part in work.parts:
        for n in part.notes:
            starts += "slur_start" in n.notations
            stops += "slur_stop" in n.notations
    assert starts > 0 and stops > 0
    assert all(
        s in {"slur_start", "slur_stop", "tie_start", "tie_stop", "fermata",
              "hairpin", "grace", "chord", "unpitched"}
        for part in work.parts
        for n in part.notes
        for s in n.notations
    )
