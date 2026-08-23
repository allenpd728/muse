"""MusicXML (.xml / .mxl) -> IR parser.

Written-note fidelity: every <note> element becomes exactly one IR Note —
tied notes stay separate (tie start/stop are flags), rests are events,
chords and grace notes are preserved. This is what the conformance registry
(corpus/README.md) pins, and what S2's lossless packing needs.

Stdlib only (xml.etree + zipfile). Swap decision: the issue context
recommended Partitura; it merges tied notes (B5: 10,115 events vs the
registry's 13,675), so a direct parser landed instead. Recorded in the
W1 commit and docs/design/w1-event-ir.md.
"""

from __future__ import annotations

import io
import os
import zipfile
from math import gcd
from xml.etree import ElementTree as ET

from .model import (
    CHORD,
    FERMATA,
    GRACE,
    HAIRPIN,
    SLUR_START,
    SLUR_STOP,
    TIE_START,
    TIE_STOP,
    UNPITCHED,
    DynamicMarking,
    Hairpin,
    Instrument,
    IRParseError,
    Maps,
    Meta,
    Note,
    Part,
    Work,
)

_STEP_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_LCM_CAP = 1_000_000


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(elem, name: str):
    return [c for c in elem if _local(c.tag) == name]


def _child(elem, name: str):
    for c in elem:
        if _local(c.tag) == name:
            return c
    return None


def _text(elem, name: str):
    c = _child(elem, name)
    return None if c is None else (c.text or "").strip()


def _lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def _read_root(source, origin: str) -> ET.Element:
    """Accept a path or file-like; transparently unwrap .mxl zip containers."""
    if hasattr(source, "read"):
        data = source.read()
        name = getattr(source, "name", origin)
    else:
        name = str(source)
        with open(source, "rb") as fh:
            data = fh.read()
    if data[:2] == b"PK":
        try:
            zf = zipfile.ZipFile(io.BytesIO(data))
        except (zipfile.BadZipFile, NotImplementedError) as exc:
            raise IRParseError(f"{name}: corrupt zip container: {exc}") from exc
        try:
            container = ET.fromstring(zf.read("META-INF/container.xml"))
        except (KeyError, ET.ParseError, zipfile.BadZipFile) as exc:
            raise IRParseError(
                f"{name}: .mxl missing or unreadable META-INF/container.xml: {exc}"
            ) from exc
        rootfile = None
        for c in container.iter():
            if _local(c.tag) == "rootfile":
                rootfile = c.attrib.get("full-path")
                break
        if not rootfile:
            raise IRParseError(f"{name}: container.xml has no rootfile entry")
        try:
            data = zf.read(rootfile)
        except (KeyError, zipfile.BadZipFile) as exc:
            raise IRParseError(
                f"{name}: rootfile {rootfile!r} not readable in container"
            ) from exc
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise IRParseError(f"{name}: malformed XML: {exc}") from exc


def load_musicxml(source, origin: str = None) -> Work:
    """Parse a MusicXML score (.xml or .mxl) into a Work. Fails loudly."""
    if origin is None:
        # Basename only: warnings ride into Work.meta and S1's canonical
        # form, so they must not embed machine-local paths.
        origin = os.path.basename(getattr(source, "name", None) or str(source))
    root = _read_root(source, origin)
    root_tag = _local(root.tag)
    if root_tag == "score-timewise":
        raise IRParseError(f"{origin}: score-timewise is not supported")
    if root_tag != "score-partwise":
        raise IRParseError(f"{origin}: expected score-partwise, got {root_tag!r}")

    ppq = _compute_ppq(root, origin)
    warnings: list = []

    work_el = _child(root, "work")
    title = _text(work_el, "work-title") if work_el is not None else None
    if title is None:
        title = _text(root, "movement-title")

    part_meta = _score_part_index(root)
    maps_acc = _MapsAccumulator(origin, warnings)

    parts = []
    for part_el in _children(root, "part"):
        pid = part_el.attrib.get("id")
        if not pid:
            raise IRParseError(f"{origin}: <part> without id")
        name, instrument = part_meta.get(pid, (pid, Instrument()))
        parts.append(_parse_part(part_el, pid, name, instrument, ppq, maps_acc, warnings, origin))

    work = Work(
        parts=parts,
        maps=maps_acc.finish(),
        meta=Meta(source_format="musicxml", ppq=ppq, title=title, warnings=warnings),
    )
    work.validate()
    return work


def _compute_ppq(root: ET.Element, origin: str) -> int:
    """Ticks per quarter = LCM of every <divisions> value in the score, so all
    integer division positions convert to integer ticks exactly."""
    ppq = 1
    for el in root.iter():
        if _local(el.tag) == "divisions" and el.text:
            try:
                d = int(el.text.strip())
            except ValueError as exc:
                raise IRParseError(
                    f"{origin}: non-integer <divisions> {el.text!r}"
                ) from exc
            if d <= 0:
                raise IRParseError(f"{origin}: non-positive <divisions> {d}")
            ppq = _lcm(ppq, d)
            if ppq > _LCM_CAP:
                raise IRParseError(
                    f"{origin}: divisions LCM exceeds {_LCM_CAP}; unsupported score"
                )
    return ppq


def _score_part_index(root: ET.Element):
    index = {}
    part_list = _child(root, "part-list")
    if part_list is None:
        return index
    for sp in _children(part_list, "score-part"):
        pid = sp.attrib.get("id")
        name = _text(sp, "part-name") or pid
        inst = Instrument(name=_text(sp, "instrument-name"))
        index[pid] = (name, inst)
    return index


class _MapsAccumulator:
    """Merge per-part map observations into work-level full maps.

    Same-tick conflicting values (sloppy encodings, e.g. one part carrying a
    stale tempo at a movement boundary) resolve first-wins with a warning;
    the map stays a single-valued function of tick."""

    def __init__(self, origin: str, warnings: list):
        self.origin = origin
        self.warnings = warnings
        self.tempo: dict = {}
        self.meter: dict = {}
        self.key: set = set()

    def add_tempo(self, tick: int, milli_bpm: int, part_id: str) -> None:
        prev = self.tempo.get(tick)
        if prev is not None and prev != milli_bpm:
            self.warnings.append(
                f"{self.origin}: conflicting tempo at tick {tick} from part {part_id}: "
                f"kept {prev}, dropped {milli_bpm} milli-bpm"
            )
            return
        self.tempo[tick] = milli_bpm

    def add_meter(self, tick: int, num: int, den: int, part_id: str) -> None:
        prev = self.meter.get(tick)
        if prev is not None and prev != (num, den):
            self.warnings.append(
                f"{self.origin}: conflicting meter at tick {tick} from part {part_id}: "
                f"kept {prev}, dropped {(num, den)}"
            )
            return
        self.meter[tick] = (num, den)

    def add_key(self, tick: int, fifths: int, mode: str) -> None:
        # Transposing parts legitimately disagree; keep every distinct value.
        self.key.add((tick, fifths, mode))

    def finish(self) -> Maps:
        return Maps(
            tempo=sorted(self.tempo.items()),
            meter=sorted((t, n, d) for t, (n, d) in self.meter.items()),
            key=sorted(self.key),
        )


def _parse_part(part_el, pid, name, instrument, ppq, maps_acc, warnings, origin) -> Part:
    part = Part(id=pid, name=name, instrument=instrument)
    divisions = None  # current MusicXML divisions (per quarter)
    cursor = 0  # ticks
    last_onset = 0
    saw_voice = False
    open_wedges: dict = {}  # wedge number -> (kind, start_tick)

    def to_ticks(divs_value: int, at) -> int:
        return divs_value * (ppq // divisions)

    def walk_direction(dir_el, tick: int) -> None:
        offset_el = _child(dir_el, "offset")
        if offset_el is not None and offset_el.text:
            tick = tick + to_ticks(int(offset_el.text.strip()), "offset")
        for dt in _children(dir_el, "direction-type"):
            for sub in dt:
                tag = _local(sub.tag)
                if tag == "dynamics":
                    text = "".join(
                        (_local(d.tag) if _local(d.tag) != "other-dynamics" else (d.text or ""))
                        for d in sub
                    )
                    part.dynamics.append(DynamicMarking(tick=tick, text=text))
                elif tag == "wedge":
                    wtype = sub.attrib.get("type", "")
                    number = sub.attrib.get("number", "1")
                    if wtype in ("crescendo", "diminuendo"):
                        open_wedges[number] = (wtype, tick)
                    elif wtype == "stop":
                        opened = open_wedges.pop(number, None)
                        if opened is not None:
                            kind, start_tick = opened
                            part.hairpins.append(
                                Hairpin(kind=kind, start_tick=start_tick, end_tick=tick)
                            )
        for snd in _children(dir_el, "sound"):
            _read_sound(snd, tick)

    def _read_sound(snd_el, tick: int) -> None:
        tempo = snd_el.attrib.get("tempo")
        if tempo:
            try:
                bpm = float(tempo)
            except ValueError as exc:
                raise IRParseError(
                    f"{origin}: part {pid}: non-numeric sound tempo {tempo!r}"
                ) from exc
            if bpm <= 0:
                raise IRParseError(f"{origin}: part {pid}: non-positive tempo {bpm}")
            maps_acc.add_tempo(tick, round(bpm * 1000), pid)

    saw_metronome = False

    for measure in _children(part_el, "measure"):
        for el in measure:
            tag = _local(el.tag)
            if tag == "attributes":
                div_el = _child(el, "divisions")
                if div_el is not None and div_el.text:
                    divisions = int(div_el.text.strip())
                key_el = _child(el, "key")
                if key_el is not None:
                    fifths_txt = _text(key_el, "fifths")
                    if fifths_txt is not None:
                        mode = _text(key_el, "mode") or "major"
                        maps_acc.add_key(cursor, int(fifths_txt), mode)
                time_el = _child(el, "time")
                if time_el is not None:
                    if _child(time_el, "senza-misura") is not None:
                        warnings.append(f"part {pid}: senza-misura time signature skipped")
                    else:
                        beats, beat_type = _text(time_el, "beats"), _text(time_el, "beat-type")
                        if beats and beat_type:
                            maps_acc.add_meter(cursor, int(beats), int(beat_type), pid)
            elif tag == "direction":
                for dt in _children(el, "direction-type"):
                    if _child(dt, "metronome") is not None:
                        saw_metronome = True
                walk_direction(el, cursor)
            elif tag == "sound":
                _read_sound(el, cursor)
            elif tag == "note":
                if divisions is None:
                    raise IRParseError(
                        f"{origin}: part {pid}: note before any <divisions> declaration"
                    )
                note, advance, onset = _parse_note(el, cursor, last_onset, to_ticks, origin, pid)
                if open_wedges:
                    note.notations = note.notations | {HAIRPIN}
                if not _has(el, "chord"):
                    last_onset = onset
                part.notes.append(note)
                cursor += advance
                if _text(el, "voice"):
                    saw_voice = True
            elif tag == "backup":
                dur = _text(el, "duration")
                if dur is None:
                    raise IRParseError(f"{origin}: part {pid}: <backup> without duration")
                cursor -= to_ticks(int(dur), "backup")
                if cursor < 0:
                    raise IRParseError(f"{origin}: part {pid}: <backup> before tick 0")
            elif tag == "forward":
                dur = _text(el, "duration")
                if dur is None:
                    raise IRParseError(f"{origin}: part {pid}: <forward> without duration")
                cursor += to_ticks(int(dur), "forward")

    for number, (kind, start) in sorted(open_wedges.items()):
        warnings.append(
            f"part {pid}: wedge {number} ({kind}) never closed; closed at part end"
        )
        part.hairpins.append(Hairpin(kind=kind, start_tick=start, end_tick=cursor))
    if saw_metronome:
        warnings.append(
            f"part {pid}: metronome mark(s) present; tempo map uses <sound tempo> values"
        )
    part.inferred_voice = not saw_voice
    part.sort_notes()
    return part


def _has(el, name: str) -> bool:
    return _child(el, name) is not None


def _parse_note(el, cursor, last_onset, to_ticks, origin, pid):
    is_chord = _has(el, "chord")
    is_grace = _has(el, "grace")
    onset = last_onset if is_chord else cursor

    dur_el = _child(el, "duration")
    if is_grace:
        duration = 0
    elif dur_el is None or not (dur_el.text or "").strip():
        raise IRParseError(f"{origin}: part {pid}: non-grace <note> without duration")
    else:
        raw = int(dur_el.text.strip())
        if raw < 0:
            raise IRParseError(f"{origin}: part {pid}: negative note duration {raw}")
        duration = to_ticks(raw, "note")

    pitch_el = _child(el, "pitch")
    unpitched = pitch_el is None and _has(el, "unpitched")
    if pitch_el is not None:
        step = _text(pitch_el, "step")
        octave_txt = _text(pitch_el, "octave")
        if step not in _STEP_SEMITONES or octave_txt is None:
            raise IRParseError(
                f"{origin}: part {pid}: malformed pitch (step={step!r}, octave={octave_txt!r})"
            )
        alter_txt = _text(pitch_el, "alter")
        alter = 0
        if alter_txt:
            alter_f = float(alter_txt)
            if alter_f != int(alter_f):
                raise IRParseError(
                    f"{origin}: part {pid}: non-integer alter {alter_txt!r} "
                    "(microtones unsupported in v0, 12-TET only)"
                )
            alter = int(alter_f)
        pitch = (int(octave_txt) + 1) * 12 + _STEP_SEMITONES[step] + alter
    else:
        pitch = None  # rest

    voice_txt = _text(el, "voice")
    notations = set()
    if is_grace:
        notations.add(GRACE)
    if unpitched:
        notations.add(UNPITCHED)
    if is_chord:
        notations.add(CHORD)
    for tie in _children(el, "tie"):
        ttype = tie.attrib.get("type", "")
        if ttype == "start":
            notations.add(TIE_START)
        elif ttype == "stop":
            notations.add(TIE_STOP)
    articulations = []
    for not_el in _children(el, "notations"):
        for art_container in _children(not_el, "articulations"):
            for art in art_container:
                articulations.append(_local(art.tag))
        for slur in _children(not_el, "slur"):
            stype = slur.attrib.get("type", "")
            if stype == "start":
                notations.add(SLUR_START)
            elif stype == "stop":
                notations.add(SLUR_STOP)
        if _child(not_el, "fermata") is not None:
            notations.add(FERMATA)

    note = Note(
        pitch=pitch,
        onset=onset,
        duration=duration,
        voice=int(voice_txt) if voice_txt else 1,
        articulations=tuple(articulations),
        notations=frozenset(notations),
        source_id=el.attrib.get("id"),
    )
    advance = 0 if is_chord else duration
    return note, advance, onset
