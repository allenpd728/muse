"""Mockup model: full DNA density (tempo map, curves, velocities, balance, note devices)."""

from __future__ import annotations

import json
import yaml
from dataclasses import dataclass, field


class MockupError(Exception):
    pass


@dataclass
class Note:
    pitch: int
    onset: int
    duration: int
    velocity: int
    onset_offset_ms: float = 0.0          # chord spread
    attack_ms: float = 0.0
    release_ms: float = 0.0
    swell: float = 0.0                    # [-1, 1] hairpin
    part: str = ""


@dataclass
class Mockup:
    work_id: str
    part_map: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)
    tempo_map: list = field(default_factory=list)
    curves: dict = field(default_factory=dict)

    def validate(self):
        if not self.notes:
            raise MockupError("empty mockup")
        for n in self.notes:
            if n.attack_ms < 0 or n.release_ms < 0:
                raise MockupError(f"negative offset on note {n.pitch}")


def add_note(mockup: Mockup, note: Note):
    mockup.notes.append(note)


def dump_mockup(mockup: Mockup, fmt="json") -> str:
    d = {
        "work_id": mockup.work_id,
        "part_map": mockup.part_map,
        "notes": [_note_to_dict(n) for n in mockup.notes],
        "tempo_map": mockup.tempo_map,
        "curves": mockup.curves,
    }
    if fmt == "json":
        return json.dumps(d, indent=2)
    return yaml.safe_dump(d, sort_keys=False, allow_unicode=True)


def load_mockup(data: str, fmt="json") -> Mockup:
    d = json.loads(data) if fmt == "json" else yaml.safe_load(data)
    m = Mockup(
        work_id=d["work_id"],
        part_map=d.get("part_map", {}),
        tempo_map=d.get("tempo_map", []),
        curves=d.get("curves", {}),
    )
    for nd in d.get("notes", []):
        m.notes.append(Note(
            pitch=nd["pitch"], onset=nd["onset"], duration=nd["duration"],
            velocity=nd.get("velocity", 64),
            onset_offset_ms=nd.get("onset_offset_ms", 0.0),
            attack_ms=nd.get("attack_ms", 0.0),
            release_ms=nd.get("release_ms", 0.0),
            swell=nd.get("swell", 0.0),
            part=nd.get("part", ""),
        ))
    return m


def _note_to_dict(n: Note):
    return {
        "pitch": n.pitch,
        "onset": n.onset,
        "duration": n.duration,
        "velocity": n.velocity,
        "onset_offset_ms": n.onset_offset_ms,
        "attack_ms": n.attack_ms,
        "release_ms": n.release_ms,
        "swell": n.swell,
        "part": n.part,
    }


def validate_mockup(mockup: Mockup, assertions: dict):
    """Check mockup against seed assertions via muse_assert."""
    from muse_assert import validate_assertions, AssertionError
    if not assertions:
        return
    # lightweight: register bounds on mockup notes
    for kind, rule in assertions.get("assertions", {}).items():
        if kind == "register":
            part = rule.get("part")
            lo = _note_to_pitch(rule["min"])
            hi = _note_to_pitch(rule["max"])
            for n in mockup.notes:
                if part and n.part and n.part != part:
                    continue
                if not (lo <= n.pitch <= hi):
                    raise AssertionError("register", f"{n.pitch} outside [{rule['min']}, {rule['max']}] in {n.part}")


_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _note_to_pitch(name):
    table = {n: i for i, n in enumerate(_NOTE_NAMES)}
    i = 1 if len(name) == 2 else 2
    return (int(name[i:]) + 1) * 12 + table[name[:i]]
