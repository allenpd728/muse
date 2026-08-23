"""Muse event-stream IR — canonical object model (W1).

Integer ticks only. Design: docs/design/w1-event-ir.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Notations flags (membership markers, raw where expressed).
TIE_START = "tie_start"
TIE_STOP = "tie_stop"
SLUR_START = "slur_start"
SLUR_STOP = "slur_stop"
FERMATA = "fermata"
HAIRPIN = "hairpin"
GRACE = "grace"
CHORD = "chord"
UNPITCHED = "unpitched"  # percussion: no MIDI pitch (staff position only)

KNOWN_NOTATIONS = frozenset(
    {TIE_START, TIE_STOP, SLUR_START, SLUR_STOP, FERMATA, HAIRPIN, GRACE, CHORD, UNPITCHED}
)

# Articulations preserved as expressed (MusicXML articulation tag names);
# validated only syntactically (non-empty strings) — the vocabulary is open.
ARTICULATION_ENUM = frozenset(
    {
        "accent",
        "strong-accent",
        "staccato",
        "tenuto",
        "detached-legato",
        "staccatissimo",
        "spiccato",
        "scoop",
        "plop",
        "doit",
        "falloff",
        "breath-mark",
        "caesura",
        "stress",
        "unstress",
        "soft-accent",
        "other-articulation",
    }
)

HAIRPIN_KINDS = frozenset({"crescendo", "diminuendo"})


class IRError(Exception):
    """Base class for IR failures."""


class IRParseError(IRError):
    """A source file is malformed or uses unsupported constructs."""


class IRValidationError(IRError):
    """An IR object violates model invariants."""


@dataclass
class Note:
    """One written note event. pitch=None marks a rest; rests are first-class
    events so a Work can reconstruct its source losslessly (S2 packs from the
    IR, never from a MIDI dump)."""

    pitch: Optional[int]  # MIDI number (12-TET); None => rest
    onset: int  # ticks
    duration: int  # ticks; 0 for grace notes
    voice: int = 1
    velocity: Optional[int] = None  # 0..127; None when the source carries none
    velocity_inferred: bool = False
    articulations: tuple = ()
    notations: frozenset = frozenset()
    source_id: Optional[str] = None  # upstream id (MusicXML id attr), if any

    @property
    def is_rest(self) -> bool:
        return self.pitch is None and UNPITCHED not in self.notations

    def sort_key(self):
        # Deterministic: (onset, pitch, velocity, lexicographic notation),
        # then voice and source id to fully break ties.
        return (
            self.onset,
            -1 if self.pitch is None else self.pitch,
            -1 if self.velocity is None else self.velocity,
            ",".join(sorted(self.notations)),
            self.voice,
            "" if self.source_id is None else self.source_id,
        )


@dataclass
class DynamicMarking:
    tick: int
    text: str  # e.g. "p", "ff", "sfz", "fp"


@dataclass
class Hairpin:
    kind: str  # "crescendo" | "diminuendo"
    start_tick: int
    end_tick: Optional[int]  # None if the source never closes it (warned)


@dataclass
class Instrument:
    name: Optional[str] = None
    gm_program: Optional[int] = None  # 0..127, MIDI sources only


@dataclass
class Part:
    id: str
    name: str
    instrument: Instrument = field(default_factory=Instrument)
    notes: list = field(default_factory=list)  # Note[], sorted deterministically
    dynamics: list = field(default_factory=list)  # DynamicMarking[], by tick
    hairpins: list = field(default_factory=list)  # Hairpin[], by start_tick
    inferred_voice: bool = False  # source carried no voice information

    def sort_notes(self) -> None:
        self.notes.sort(key=lambda n: n.sort_key())
        self.dynamics.sort(key=lambda d: d.tick)
        self.hairpins.sort(key=lambda h: h.start_tick)


@dataclass
class Maps:
    """Full maps — mid-piece changes preserved. tempo: (tick, bpm*1000).
    meter: (tick, numerator, denominator). key: (tick, fifths, mode).

    Tempo and meter are score-global: same-tick conflicts are corruption and
    fail loudly. Key may legitimately differ across parts at one tick
    (transposing instruments); the key map therefore keeps one entry per
    distinct (tick, fifths, mode) and is ordered by (tick, fifths, mode)."""

    tempo: list = field(default_factory=list)
    meter: list = field(default_factory=list)
    key: list = field(default_factory=list)


@dataclass
class Meta:
    source_format: str  # "musicxml" | "midi"
    ppq: int  # ticks per quarter note for this Work
    title: Optional[str] = None
    warnings: list = field(default_factory=list)


@dataclass
class Work:
    parts: list = field(default_factory=list)  # Part[]
    maps: Maps = field(default_factory=Maps)
    meta: Optional[Meta] = None

    @property
    def note_count(self) -> int:
        return sum(len(p.notes) for p in self.parts)

    def validate(self) -> None:
        """Fail loudly on invariant violations. Called by parsers before
        returning; downstream tools may re-validate after transforms."""
        if self.meta is None:
            raise IRValidationError("Work.meta is required")
        if self.meta.ppq <= 0:
            raise IRValidationError(f"ppq must be positive, got {self.meta.ppq}")
        if not self.parts:
            raise IRValidationError("Work has no parts")
        seen_part_ids = set()
        for part in self.parts:
            if part.id in seen_part_ids:
                raise IRValidationError(f"duplicate part id {part.id!r}")
            seen_part_ids.add(part.id)
            for n in part.notes:
                if n.pitch is not None and not (0 <= n.pitch <= 127):
                    raise IRValidationError(
                        f"part {part.id}: pitch {n.pitch} out of range 0..127"
                    )
                if n.duration < 0:
                    raise IRValidationError(
                        f"part {part.id}: negative duration {n.duration}"
                    )
                if n.onset < 0:
                    raise IRValidationError(f"part {part.id}: negative onset {n.onset}")
                if n.velocity is not None and not (0 <= n.velocity <= 127):
                    raise IRValidationError(
                        f"part {part.id}: velocity {n.velocity} out of range 0..127"
                    )
                unknown = n.notations - KNOWN_NOTATIONS
                if unknown:
                    raise IRValidationError(
                        f"part {part.id}: unknown notations {sorted(unknown)}"
                    )
            keys = [n.sort_key() for n in part.notes]
            if keys != sorted(keys):
                raise IRValidationError(
                    f"part {part.id}: notes not in deterministic order"
                )
        _validate_strict_map(self.maps.tempo, "tempo")
        _validate_strict_map(self.maps.meter, "meter")
        key_ticks = [k[0] for k in self.maps.key]
        if key_ticks != sorted(key_ticks):
            raise IRValidationError("key map not ordered by tick")

    def duration_ticks(self) -> int:
        end = 0
        for p in self.parts:
            for n in p.notes:
                end = max(end, n.onset + n.duration)
        for entry in self.maps.tempo + self.maps.meter + self.maps.key:
            end = max(end, entry[0])
        return end


def _validate_strict_map(entries, name: str) -> None:
    ticks = [e[0] for e in entries]
    if ticks != sorted(ticks):
        raise IRValidationError(f"{name} map not ordered by tick")
    if len(set(ticks)) != len(ticks):
        raise IRValidationError(f"{name} map has duplicate ticks")
