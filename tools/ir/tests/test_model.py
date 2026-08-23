"""Model invariants: deterministic ordering and validation hooks."""

import pytest

from muse_ir import IRValidationError, Maps, Meta, Note, Part, Work


def make_work(notes, **meta_kwargs):
    part = Part(id="P1", name="P1", notes=list(notes))
    part.sort_notes()
    meta = Meta(source_format="musicxml", ppq=480, **meta_kwargs)
    return Work(parts=[part], maps=Maps(), meta=meta)


def test_deterministic_sort_order():
    notes = [
        Note(pitch=64, onset=10, duration=5),
        Note(pitch=60, onset=10, duration=5),
        Note(pitch=60, onset=0, duration=5),
        Note(pitch=None, onset=5, duration=5),  # rest sorts before pitched at same onset
    ]
    work = make_work(notes)
    ordered = work.parts[0].notes
    assert [(n.onset, n.pitch) for n in ordered] == [
        (0, 60),
        (5, None),
        (10, 60),
        (10, 64),
    ]
    work.validate()  # sorted notes pass


def test_notations_tiebreak_is_deterministic():
    a = Note(pitch=60, onset=0, duration=5, notations=frozenset({"tie_start"}))
    b = Note(pitch=60, onset=0, duration=5)
    work = make_work([a, b])
    ordered = work.parts[0].notes
    assert ordered[0].notations == frozenset()  # "" < "tie_start"
    assert ordered[1].notations == frozenset({"tie_start"})


def test_validate_rejects_negative_duration():
    work = make_work([Note(pitch=60, onset=0, duration=-1)])
    with pytest.raises(IRValidationError, match="negative duration"):
        work.validate()


def test_validate_rejects_pitch_out_of_range():
    work = make_work([Note(pitch=128, onset=0, duration=1)])
    with pytest.raises(IRValidationError, match="pitch"):
        work.validate()


def test_validate_rejects_velocity_out_of_range():
    work = make_work([Note(pitch=60, onset=0, duration=1, velocity=200)])
    with pytest.raises(IRValidationError, match="velocity"):
        work.validate()


def test_validate_rejects_unknown_notations():
    work = make_work([Note(pitch=60, onset=0, duration=1, notations=frozenset({"bogus"}))])
    with pytest.raises(IRValidationError, match="notations"):
        work.validate()


def test_validate_rejects_unsorted_notes():
    part = Part(
        id="P1",
        name="P1",
        notes=[Note(pitch=64, onset=10, duration=1), Note(pitch=60, onset=0, duration=1)],
    )  # deliberately not sort_notes()'d
    work = Work(parts=[part], maps=Maps(), meta=Meta(source_format="musicxml", ppq=480))
    with pytest.raises(IRValidationError, match="deterministic order"):
        work.validate()


def test_validate_rejects_duplicate_part_ids():
    part = Part(id="P1", name="a", notes=[Note(pitch=60, onset=0, duration=1)])
    part2 = Part(id="P1", name="b", notes=[Note(pitch=60, onset=0, duration=1)])
    work = Work(parts=[part, part2], maps=Maps(), meta=Meta(source_format="midi", ppq=96))
    with pytest.raises(IRValidationError, match="duplicate part id"):
        work.validate()


def test_validate_rejects_unordered_tempo_map():
    work = make_work([Note(pitch=60, onset=0, duration=1)])
    work.maps.tempo = [(100, 120000), (50, 96000)]
    with pytest.raises(IRValidationError, match="tempo map not ordered"):
        work.validate()


def test_validate_rejects_duplicate_tempo_ticks():
    work = make_work([Note(pitch=60, onset=0, duration=1)])
    work.maps.tempo = [(0, 120000), (0, 96000)]
    with pytest.raises(IRValidationError, match="duplicate ticks"):
        work.validate()


def test_validate_rejects_empty_work():
    work = Work(parts=[], maps=Maps(), meta=Meta(source_format="musicxml", ppq=480))
    with pytest.raises(IRValidationError, match="no parts"):
        work.validate()


def test_unpitched_note_is_not_a_rest():
    percussion = Note(pitch=None, onset=0, duration=10, notations=frozenset({"unpitched"}))
    rest = Note(pitch=None, onset=0, duration=10)
    assert not percussion.is_rest
    assert rest.is_rest
    make_work([percussion, rest]).validate()


def test_load_rejects_unsupported_extension(tmp_path):
    from muse_ir import IRParseError, load

    bad = tmp_path / "score.pdf"
    bad.write_bytes(b"%PDF-1.4")
    with pytest.raises(IRParseError, match="unsupported source format"):
        load(str(bad))
