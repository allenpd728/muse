"""IR data model. Integer ticks only; deterministic ordering; validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


class ValidationError(ValueError):
    """Raised when an IR structure violates invariants."""


@dataclass(frozen=True)
class Note:
    pitch: int                      # MIDI number (12-TET v0); -1 = rest; -2 = unpitched
    onset: int                      # ticks
    duration: int                   # ticks
    velocity: Optional[int] = None  # 0..127; None = inferred (MIDI-only)
    articulation: Optional[str] = None
    notations: tuple = ()           # tie, slur, fermata, grace, unpitched flags
    voice: Optional[int] = None     # within-part voice index

    def __post_init__(self):
        if self.duration < 0:
            raise ValidationError(f"negative duration: {self.duration}")
        if not (-2 <= self.pitch <= 127):
            raise ValidationError(f"pitch out of range: {self.pitch}")
        if self.velocity is not None and not (0 <= self.velocity <= 127):
            raise ValidationError(f"velocity out of range: {self.velocity}")

    @property
    def is_rest(self) -> bool:
        return self.pitch == -1

    @property
    def is_unpitched(self) -> bool:
        return self.pitch == -2


@dataclass
class Part:
    id: str
    name: str
    gm_program: Optional[int] = None
    notes: list = field(default_factory=list)  # list[Note]

    def sort_notes(self):
        """Deterministic order: onset, then pitch, then voice."""
        self.notes.sort(key=lambda n: (n.onset, n.pitch, n.voice or 0))


@dataclass
class Maps:
    tempo: list = field(default_factory=list)   # [(tick, milli_bpm)]
    meter: list = field(default_factory=list)   # [(tick, num, den)]
    key: list = field(default_factory=list)     # [(tick, fifths, mode)]

    def validate(self):
        for name, seq in (("tempo", self.tempo), ("meter", self.meter), ("key", self.key)):
            ticks = [e[0] for e in seq]
            if ticks != sorted(ticks):
                raise ValidationError(f"{name} map not ordered by tick")


@dataclass
class Work:
    parts: list = field(default_factory=list)   # list[Part]
    maps: Maps = field(default_factory=Maps)
    source_format: str = "unknown"              # "musicxml" | "midi"
    ppq: int = 480                              # ticks per quarter
    title: Optional[str] = None
    warnings: list = field(default_factory=list)

    def validate(self):
        self.maps.validate()
        for p in self.parts:
            for n in p.notes:
                if n.onset < 0:
                    raise ValidationError(f"negative onset in part {p.id}")

    def finalize(self):
        """Sort notes in every part and validate the whole work."""
        for p in self.parts:
            p.sort_notes()
        self.validate()
        return self

    @property
    def note_count(self) -> int:
        return sum(len(p.notes) for p in self.parts)
