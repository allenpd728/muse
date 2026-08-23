"""Unit tests for the MusicXML parser: written-note fidelity (ties, chords,
grace, rests), cursor math (backup/forward, mid-part division changes),
full maps, .mxl container handling, and loud failure on malformed input."""

import io
import zipfile

import pytest

from muse_ir import IRParseError, load_musicxml

SCORE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <work><work-title>{title}</work-title></work>
  <part-list>
    <score-part id="P1"><part-name>Flute</part-name></score-part>
  </part-list>
  <part id="P1">
    {measures}
  </part>
</score-partwise>
"""

ATTRIBUTES = """
      <attributes>
        <divisions>{divisions}</divisions>
        <key><fifths>{fifths}</fifths><mode>{mode}</mode></key>
        <time><beats>{beats}</beats><beat-type>{beat_type}</beat-type></time>
      </attributes>"""


def make_score(measures: str, title="Unit Test") -> str:
    return SCORE_TEMPLATE.format(title=title, measures=measures)


def make_measure(body: str, number=1) -> str:
    return f'<measure number="{number}">{body}</measure>'


def note(step="C", octave=4, duration=1, extra="", pitch_extra=""):
    pitch = (
        f"<pitch><step>{step}</step>{pitch_extra}<octave>{octave}</octave></pitch>"
        if step is not None
        else "<rest/>"
    )
    dur = f"<duration>{duration}</duration>" if duration is not None else ""
    return f"<note>{pitch}{dur}{extra}</note>"


def test_basic_notes_and_maps():
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=2, fifths=0, mode="major", beats=4, beat_type=4)
            + '<direction><sound tempo="120"/></direction>'
            + note("C", 4, 2)
            + note("E", 4, 2)
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    assert len(work.parts) == 1
    part = work.parts[0]
    assert [n.pitch for n in part.notes] == [60, 64]
    assert [n.onset for n in part.notes] == [0, 2]
    assert work.meta.ppq == 2
    assert work.meta.title == "Unit Test"
    assert work.maps.tempo == [(0, 120000)]
    assert work.maps.meter == [(0, 4, 4)]
    assert work.maps.key == [(0, 0, "major")]


def test_rests_are_events():
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + note("C", 4, 1)
            + note(None, None, 1)
            + note("G", 4, 1)
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    part = work.parts[0]
    assert work.note_count == 3
    assert part.notes[1].is_rest
    assert part.notes[2].onset == 2


def test_ties_stay_separate_with_flags():
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + note("C", 4, 2, extra='<tie type="start"/>')
            + note("C", 4, 2, extra='<tie type="stop"/>')
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    notes = work.parts[0].notes
    assert len(notes) == 2
    assert "tie_start" in notes[0].notations
    assert "tie_stop" in notes[1].notations
    assert notes[1].onset == 2


def test_chord_members_share_onset():
    chord_note = (
        "<note><chord/><pitch><step>E</step><octave>4</octave></pitch>"
        "<duration>2</duration></note>"
    )
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=2, fifths=0, mode="major", beats=4, beat_type=4)
            + note("C", 4, 2)
            + chord_note
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    notes = work.parts[0].notes
    assert [n.onset for n in notes] == [0, 0]
    assert "chord" in notes[1].notations


def test_grace_notes_zero_duration():
    grace = (
        "<note><grace/><pitch><step>D</step><octave>4</octave></pitch></note>"
    )
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=2, fifths=0, mode="major", beats=4, beat_type=4)
            + grace
            + note("C", 4, 2)
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    notes = work.parts[0].notes
    grace_note = next(n for n in notes if "grace" in n.notations)
    assert grace_note.pitch == 62
    assert grace_note.duration == 0
    main = next(n for n in notes if "grace" not in n.notations)
    assert main.onset == 0  # grace notes do not advance the cursor


def test_backup_multi_voice_cursor():
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + note("C", 5, 4, extra="<voice>1</voice>")
            + "<backup><duration>4</duration></backup>"
            + note("E", 3, 4, extra="<voice>2</voice>")
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    notes = work.parts[0].notes
    assert {(n.pitch, n.onset, n.voice) for n in notes} == {(72, 0, 1), (52, 0, 2)}


def test_mid_part_divisions_change_stays_integral():
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=2, fifths=0, mode="major", beats=4, beat_type=4)
            + note("C", 4, 2)
            + "<attributes><divisions>6</divisions></attributes>"
            + note("D", 4, 3)
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    assert work.meta.ppq == 6  # lcm(2, 6)
    notes = work.parts[0].notes
    assert notes[0].duration == 6  # 2 divs * (6 // 2)
    assert notes[1].onset == 6
    assert notes[1].duration == 3  # 3 divs * (6 // 6)


def test_pitch_alter_accidentals():
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + note("F", 4, 1, pitch_extra="<alter>1</alter>")
            + note("B", 3, 1, pitch_extra="<alter>-1</alter>")
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    assert [n.pitch for n in work.parts[0].notes] == [66, 58]


def test_dynamics_and_hairpins():
    direction = (
        '<direction><direction-type><dynamics><f/></dynamics></direction-type>'
        '<sound tempo="96"/></direction>'
        + '<direction><direction-type><wedge type="crescendo" number="1"/></direction-type></direction>'
    )
    stop = '<direction><direction-type><wedge type="stop" number="1"/></direction-type></direction>'
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + direction
            + note("C", 4, 2)
            + stop
            + note("D", 4, 2)
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    part = work.parts[0]
    assert [(d.tick, d.text) for d in part.dynamics] == [(0, "f")]
    assert len(part.hairpins) == 1
    assert part.hairpins[0].kind == "crescendo"
    assert part.hairpins[0].start_tick == 0
    assert part.hairpins[0].end_tick == 2
    assert "hairpin" in part.notes[0].notations
    assert "hairpin" not in part.notes[1].notations


def test_articulations_and_slur_fermata_flags():
    extra = (
        "<notations>"
        "<articulations><staccato/><accent/></articulations>"
        '<slur type="start" number="1"/>'
        "<fermata/>"
        "</notations>"
    )
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + note("C", 4, 1, extra=extra)
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    n = work.parts[0].notes[0]
    assert n.articulations == ("staccato", "accent")
    assert {"slur_start", "fermata"} <= n.notations


def test_mxl_container_round_trip(tmp_path):
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + note("C", 4, 4)
        )
    )
    mxl = tmp_path / "t.mxl"
    with zipfile.ZipFile(mxl, "w") as zf:
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container><rootfiles>'
            '<rootfile full-path="score.xml" media-type="application/vnd.recordare.musicxml+xml"/>'
            "</rootfiles></container>",
        )
        zf.writestr("score.xml", xml)
    work = load_musicxml(str(mxl))
    assert work.note_count == 1
    assert work.parts[0].notes[0].pitch == 60


def test_unpitched_percussion_is_not_a_rest():
    unpitched = (
        "<note><unpitched><display-step>B</display-step>"
        "<display-octave>4</display-octave></unpitched>"
        "<duration>1</duration></note>"
    )
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + unpitched
            + note(None, None, 1)
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    percussion, rest = work.parts[0].notes
    assert percussion.pitch is None
    assert "unpitched" in percussion.notations
    assert not percussion.is_rest
    assert rest.is_rest


def test_inferred_voice_flag_when_source_has_no_voices():
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + note("C", 4, 1)
        )
    )
    work = load_musicxml(io.BytesIO(xml.encode()), origin="test")
    assert work.parts[0].inferred_voice


# --- malformed inputs fail loudly ---


def test_malformed_xml_fails():
    with pytest.raises(IRParseError, match="malformed XML"):
        load_musicxml(io.BytesIO(b"<score-partwise><part"), origin="bad")


def test_timewise_fails():
    with pytest.raises(IRParseError, match="score-timewise"):
        load_musicxml(io.BytesIO(b"<score-timewise></score-timewise>"), origin="bad")


def test_note_without_duration_fails():
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + note("C", 4, None)
        )
    )
    with pytest.raises(IRParseError, match="without duration"):
        load_musicxml(io.BytesIO(xml.encode()), origin="bad")


def test_note_before_divisions_fails():
    xml = make_score(make_measure(note("C", 4, 1)))
    with pytest.raises(IRParseError, match="divisions"):
        load_musicxml(io.BytesIO(xml.encode()), origin="bad")


def test_microtonal_alter_fails():
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + note("C", 4, 1, pitch_extra="<alter>0.5</alter>")
        )
    )
    with pytest.raises(IRParseError, match="microtones"):
        load_musicxml(io.BytesIO(xml.encode()), origin="bad")


def test_backup_before_zero_fails():
    xml = make_score(
        make_measure(
            ATTRIBUTES.format(divisions=1, fifths=0, mode="major", beats=4, beat_type=4)
            + "<backup><duration>8</duration></backup>"
            + note("C", 4, 1)
        )
    )
    with pytest.raises(IRParseError, match="backup"):
        load_musicxml(io.BytesIO(xml.encode()), origin="bad")


def test_corrupt_zip_fails(tmp_path):
    bad = tmp_path / "bad.mxl"
    bad.write_bytes(b"PK\x03\x04" + b"\x00" * 8)
    with pytest.raises(IRParseError):
        load_musicxml(str(bad))


def test_mxl_missing_container_fails(tmp_path):
    bad = tmp_path / "nocontainer.mxl"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("score.xml", "<score-partwise/>")
    with pytest.raises(IRParseError, match="container"):
        load_musicxml(str(bad))
