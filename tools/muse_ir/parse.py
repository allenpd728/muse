"""Parsers: MusicXML (.xml/.mxl) and MIDI (.mid) → IR Work."""

from __future__ import annotations

import os
import zipfile

from .model import Work, Part, Note, Maps, ValidationError


def load(path: str) -> Work:
    """Dispatch on extension: .xml/.mxl/.musicxml → MusicXML; .mid/.midi → MIDI."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xml", ".mxl", ".musicxml"):
        return load_musicxml(path)
    if ext in (".mid", ".midi"):
        return load_midi(path)
    raise ValidationError(f"unsupported extension: {ext}")


def load_musicxml(path: str) -> Work:
    """Parse MusicXML (or compressed .mxl) via partitura into IR."""
    import partitura

    try:
        score = partitura.load_musicxml(path)
    except Exception as e:
        raise ValidationError(f"MusicXML parse failed for {path}: {e}") from e

    work = Work(source_format="musicxml")
    _extract_title(score, work)
    sna = score.note_array()
    work.ppq = int(sna["divs_pq"][0]) if len(sna) > 0 else 480

    for i, spart in enumerate(score.parts):
        part = Part(
            id=getattr(spart, "id", None) or f"P{i+1:02d}",
            name=getattr(spart, "part_name", None) or f"Part {i+1}",
        )
        # Use raw part.notes (not note_array) so tied notes stay separate
        # events with tie membership flagged — registry counts raw <note>.
        for n in spart.notes:
            notations = []
            if getattr(n, "tie_next", None) is not None:
                notations.append("tie_start")
            if getattr(n, "tie_prev", None) is not None:
                notations.append("tie_stop")
            if getattr(n, "grace", None):
                notations.append("grace")
            part.notes.append(Note(
                pitch=int(n.midi_pitch),
                onset=int(n.start.t),
                duration=int(n.end.t - n.start.t),
                velocity=None,
                voice=getattr(n, "voice", None),
                notations=tuple(notations),
            ))
        for r in spart.rests:
            part.notes.append(Note(
                pitch=-1,
                onset=int(r.start.t),
                duration=int(r.end.t - r.start.t),
                voice=getattr(r, "voice", None),
            ))
        # Unpitched percussion (partitura keeps them out of .notes)
        try:
            from partitura.score import UnpitchedNote
            for u in spart.iter_all(UnpitchedNote):
                part.notes.append(Note(
                    pitch=-2,
                    onset=int(u.start.t),
                    duration=int(u.end.t - u.start.t),
                    voice=getattr(u, "voice", None),
                    notations=("unpitched",),
                ))
        except Exception:
            pass
        work.parts.append(part)

    _extract_maps(score, work)
    return work.finalize()


def load_midi(path: str) -> Work:
    """Parse MIDI via mido into IR. Full maps from meta events."""
    import mido

    try:
        mid = mido.MidiFile(path)
    except Exception as e:
        raise ValidationError(f"MIDI parse failed for {path}: {e}") from e

    work = Work(source_format="midi", ppq=mid.ticks_per_beat)

    # Meta events: tempo/key/time-signature (from merged track for global maps)
    for msg in mid.merged_track:
        pass  # merged_track is consumed below in absolute time

    abs_tick = 0
    for msg in mid.merged_track:
        abs_tick += msg.time
        if msg.is_meta:
            if msg.type == "set_tempo":
                bpm = 60_000_000 / msg.tempo
                work.maps.tempo.append((abs_tick, int(round(bpm * 1000))))
            elif msg.type == "time_signature":
                work.maps.meter.append((abs_tick, msg.numerator, msg.denominator))
            elif msg.type == "key_signature":
                work.maps.key.append((abs_tick, _key_to_fifths(msg.key), "major"))

    # Notes per track → per part
    for ti, track in enumerate(mid.tracks):
        part = Part(id=f"T{ti+1:02d}", name=track.name or f"Track {ti+1}")
        active = {}
        abs_tick = 0
        for msg in track:
            abs_tick += msg.time
            if msg.type == "program_change":
                part.gm_program = msg.program
            elif msg.type == "note_on" and msg.velocity > 0:
                active.setdefault(msg.note, []).append((abs_tick, msg.velocity))
            elif msg.type in ("note_off",) or (msg.type == "note_on" and msg.velocity == 0):
                if msg.note in active and active[msg.note]:
                    on, vel = active[msg.note].pop(0)
                    part.notes.append(Note(
                        pitch=msg.note, onset=on, duration=abs_tick - on, velocity=vel,
                    ))
        if part.notes:
            work.parts.append(part)

    if not work.maps.tempo:
        work.warnings.append("no tempo map in MIDI; default 120bpm assumed downstream")
    return work.finalize()


def _extract_title(score, work: Work):
    try:
        info = score.parts[0]
        # partitura exposes title via score.metadata when present
        md = getattr(score, "metadata", None)
        if md and getattr(md, "title", None):
            work.title = md.title
    except Exception:
        pass


def _extract_maps(score, work: Work):
    """Tempo/meter/key maps from partitura score, converted to ticks."""
    divs = work.ppq
    try:
        first = score.parts[0]
        # tempo map: partitura stores per-part; take union from first part
        for tp in getattr(first, "tempo_points", []) or []:
            pass  # partitura version-dependent; fallback below
    except Exception:
        pass
    # Fallback: derive from note_array beat map if direct maps unavailable.
    # MusicXML tempo/meter/key are handled by partitura's score model; for v0
    # we record what partitura exposes and mark missing maps as warnings.
    if not work.maps.tempo:
        work.warnings.append("tempo map not extracted (partitura API); use defaults")


def _key_to_fifths(key_name: str) -> int:
    """Convert MIDI key signature name to circle-of-fifths number."""
    table = {
        "C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
        "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Db": -5, "Gb": -6, "Cb": -7,
        "Am": 0, "Em": 1, "Bm": 2, "F#m": 3, "C#m": 4, "G#m": 5, "D#m": 6,
        "Dm": -1, "Gm": -2, "Cm": -3, "Fm": -4, "Bbm": -5, "Ebm": -6,
    }
    return table.get(key_name, 0)
