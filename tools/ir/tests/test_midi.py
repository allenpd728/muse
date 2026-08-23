"""Unit tests for the MIDI parser: full maps from meta events, part/track
derivation, note pairing, and loud failure on malformed files."""

import io
import struct

import mido
import pytest

from muse_ir import IRParseError, load_midi


def make_midi(tracks, tpb=480, mtype=1) -> bytes:
    mid = mido.MidiFile(type=mtype, ticks_per_beat=tpb)
    for msgs in tracks:
        track = mido.MidiTrack()
        for msg in msgs:
            track.append(msg)
        mid.tracks.append(track)
    buf = io.BytesIO()
    mid.save(file=buf)
    return buf.getvalue()


def conductor_track():
    return [
        mido.MetaMessage("track_name", name="Test Work", time=0),
        mido.MetaMessage("set_tempo", tempo=500000, time=0),
        mido.MetaMessage("time_signature", numerator=3, denominator=4, time=0),
        mido.MetaMessage("key_signature", key="Dm", time=0),
        mido.MetaMessage("set_tempo", tempo=400000, time=960),
    ]


def voice_track(name, program, notes):
    msgs = [mido.MetaMessage("track_name", name=name, time=0)]
    msgs.append(mido.Message("program_change", program=program, channel=0, time=0))
    for onset, pitch, dur, vel in notes:
        msgs.append(mido.Message("note_on", note=pitch, velocity=vel, channel=0, time=onset))
        msgs.append(mido.Message("note_off", note=pitch, velocity=0, channel=0, time=dur))
    return msgs


def test_full_maps_and_parts():
    data = make_midi(
        [
            conductor_track(),
            voice_track("Soprano", 52, [(0, 60, 240, 80), (480, 62, 240, 90)]),
            voice_track("Bass", 58, [(0, 36, 480, 70)]),
        ]
    )
    work = load_midi(io.BytesIO(data), origin="test.mid")
    assert work.meta.source_format == "midi"
    assert work.meta.ppq == 480
    assert work.meta.title == "Test Work"
    assert [p.name for p in work.parts] == ["Soprano", "Bass"]
    assert work.parts[0].instrument.gm_program == 52
    assert work.maps.tempo == [(0, 120000), (960, 150000)]
    assert work.maps.meter == [(0, 3, 4)]
    assert work.maps.key == [(0, -1, "minor")]
    n = work.parts[0].notes[0]
    assert (n.pitch, n.onset, n.duration, n.velocity) == (60, 0, 240, 80)
    assert not n.velocity_inferred


def test_note_on_velocity_zero_pairs_as_off():
    data = make_midi(
        [
            conductor_track(),
            [
                mido.MetaMessage("track_name", name="V", time=0),
                mido.Message("note_on", note=64, velocity=100, channel=0, time=0),
                mido.Message("note_on", note=64, velocity=0, channel=0, time=120),
            ],
        ]
    )
    work = load_midi(io.BytesIO(data), origin="test.mid")
    assert work.parts[0].notes[0].duration == 120


def test_overlapping_same_pitch_notes_pair_fifo():
    data = make_midi(
        [
            conductor_track(),
            [
                mido.MetaMessage("track_name", name="V", time=0),
                mido.Message("note_on", note=60, velocity=70, channel=0, time=0),
                mido.Message("note_on", note=60, velocity=80, channel=0, time=100),
                mido.Message("note_off", note=60, velocity=0, channel=0, time=100),
                mido.Message("note_off", note=60, velocity=0, channel=0, time=200),
            ],
        ]
    )
    work = load_midi(io.BytesIO(data), origin="test.mid")
    notes = work.parts[0].notes
    # note_off at t=200 closes the first note_on; note_off at t=400 the second
    assert [(n.onset, n.duration, n.velocity) for n in notes] == [
        (0, 200, 70),
        (100, 300, 80),
    ]


def test_control_tracks_do_not_become_parts():
    data = make_midi(
        [
            conductor_track(),
            [mido.MetaMessage("track_name", name="Tempo control", time=0)],
            voice_track("Alto", 50, [(0, 57, 120, 64)]),
        ]
    )
    work = load_midi(io.BytesIO(data), origin="test.mid")
    assert [p.name for p in work.parts] == ["Alto"]


def test_missing_tempo_inserts_default_with_warning():
    data = make_midi([voice_track("V", 0, [(0, 60, 120, 64)])])
    work = load_midi(io.BytesIO(data), origin="test.mid")
    assert work.maps.tempo == [(0, 120000)]
    assert work.maps.meter == [(0, 4, 4)]
    assert any("120 bpm" in w for w in work.meta.warnings)


# --- malformed inputs fail loudly ---


def test_garbage_bytes_fail():
    with pytest.raises(IRParseError, match="unreadable MIDI"):
        load_midi(io.BytesIO(b"this is not a midi file"), origin="bad.mid")


def test_note_off_without_on_fails():
    data = make_midi(
        [
            conductor_track(),
            [
                mido.MetaMessage("track_name", name="V", time=0),
                mido.Message("note_off", note=60, velocity=0, channel=0, time=0),
            ],
        ]
    )
    with pytest.raises(IRParseError, match="note_off without note_on"):
        load_midi(io.BytesIO(data), origin="bad.mid")


def test_dangling_note_on_fails():
    data = make_midi(
        [
            conductor_track(),
            [
                mido.MetaMessage("track_name", name="V", time=0),
                mido.Message("note_on", note=60, velocity=90, channel=0, time=0),
            ],
        ]
    )
    with pytest.raises(IRParseError, match="never closed"):
        load_midi(io.BytesIO(data), origin="bad.mid")


def test_smpte_division_fails():
    data = make_midi([voice_track("V", 0, [(0, 60, 120, 64)])], tpb=-25)
    with pytest.raises(IRParseError, match="SMPTE"):
        load_midi(io.BytesIO(data), origin="bad.mid")


def test_type2_fails():
    data = make_midi([voice_track("V", 0, [(0, 60, 120, 64)])], mtype=2)
    with pytest.raises(IRParseError, match="type 2"):
        load_midi(io.BytesIO(data), origin="bad.mid")


def test_unknown_key_signature_fails():
    # mido validates key names at message construction, so corrupt bytes are
    # hand-built: a key_signature meta event carrying "H#".
    track = bytes(
        [
            0x00, 0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20,  # set_tempo 500000
            0x00, 0xFF, 0x59, 0x02, 0x48, 0x23,  # key_signature "H#"
            0x00, 0x90, 60, 90,  # note_on
            0x83, 0x60, 0x80, 60, 0,  # note_off, 480 ticks later
            0x00, 0xFF, 0x2F, 0x00,  # end of track
        ]
    )
    data = (
        b"MThd"
        + struct.pack(">IHHH", 6, 0, 1, 480)
        + b"MTrk"
        + struct.pack(">I", len(track))
        + track
    )
    with pytest.raises(IRParseError, match="unreadable MIDI"):
        load_midi(io.BytesIO(data), origin="bad.mid")
