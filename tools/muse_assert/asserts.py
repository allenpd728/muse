"""Assertion evaluation: seed assertions vs. an IR work."""

from __future__ import annotations


class AssertionError(AssertionError if False else Exception):
    """Raised when a performance violates a seed assertion."""

    def __init__(self, kind, detail):
        super().__init__(f"assertion failed [{kind}]: {detail}")
        self.kind = kind


def _pitch_to_note_name(pitch):
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return names[pitch % 12] + str(pitch // 12 - 1)


def _note_name_to_pitch(name):
    table = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
             "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    i = 1 if len(name) == 2 else 2
    base = table[name[:i]]
    octave = int(name[i:])
    return (octave + 1) * 12 + base


def validate_assertions(work, assertions: dict):
    """Evaluate assertions dict against work. Any failure raises AssertionError.

    Supported kinds: must_contain (theme refs as pitch sequences), register
    (part pitch bounds), form (section presence), max_tempo/min_tempo bounds.
    """
    if not assertions:
        return
    for kind, val in assertions.items():
        if kind == "must_contain":
            _check_must_contain(work, val)
        elif kind == "register":
            _check_register(work, val)
        elif kind == "form":
            _check_form(work, val)
        elif kind == "tempo_bounds":
            _check_tempo_bounds(work, val)
        else:
            raise AssertionError("unknown-assertion-kind", kind)


def _check_must_contain(work, themes):
    """Each theme (list of pitches) must appear in some part."""
    all_pitches = []
    for p in work.parts:
        all_pitches.extend([n.pitch for n in p.notes
                            if n.pitch is not None and not getattr(n, "is_rest", False)])
    for theme in themes:
        seq = theme if isinstance(theme, list) else theme.get("pitches", [])
        ok = any(
            all_pitches[i:i + len(seq)] == seq
            for i in range(len(all_pitches) - len(seq) + 1)
        )
        if not ok:
            raise AssertionError("must_contain", f"theme {seq} not found")


def _check_register(work, bounds):
    """Part(s) pitch must stay within [min, max] note names."""
    part = bounds.get("part")
    lo = _note_name_to_pitch(bounds["min"])
    hi = _note_name_to_pitch(bounds["max"])
    for p in work.parts:
        if part and p.id != part and p.name != part:
            continue
        for n in p.notes:
            if n.pitch is None or getattr(n, "is_rest", False) or getattr(n, "is_unpitched", False):
                continue
            if not (lo <= n.pitch <= hi):
                raise AssertionError("register", f"{p.id} note {n.pitch} outside [{bounds['min']}, {bounds['max']}]")


def _check_form(work, spec):
    """Section markers present (sections list or repeat count)."""
    sections = spec.get("sections", [])
    if not sections:
        return
    found = set()
    for p in work.parts:
        for n in p.notes:
            for sec in sections:
                if str(n.onset) in str(sec) or sec in getattr(n, "notations", ()):
                    found.add(sec)
    missing = set(sections) - found
    if missing:
        raise AssertionError("form", f"missing sections {sorted(missing)}")


def _check_tempo_bounds(work, bounds):
    lo = bounds.get("min_bpm")
    hi = bounds.get("max_bpm")
    for tick, milli_bpm in work.maps.tempo:
        bpm = milli_bpm / 1000
        if lo and bpm < lo:
            raise AssertionError("tempo_bounds", f"tempo {bpm} < {lo}")
        if hi and bpm > hi:
            raise AssertionError("tempo_bounds", f"tempo {bpm} > {hi}")
