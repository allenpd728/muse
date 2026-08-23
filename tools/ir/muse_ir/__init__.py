"""muse_ir — Muse event-stream IR (W1).

Canonical in-memory event format shared by every tool in the repo
(W2 loader, W3 analyzer, W4 diff, W5 visualizer). Integer ticks only.

    from muse_ir import load
    work = load("corpus/bach/bwv227.1.mxl")
"""

from __future__ import annotations

import os

from .midi import load_midi
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
    IRError,
    IRParseError,
    IRValidationError,
    Maps,
    Meta,
    Note,
    Part,
    Work,
)
from .musicxml import load_musicxml

__all__ = [
    "load",
    "load_musicxml",
    "load_midi",
    "Work",
    "Part",
    "Note",
    "Maps",
    "Meta",
    "Instrument",
    "DynamicMarking",
    "Hairpin",
    "IRError",
    "IRParseError",
    "IRValidationError",
    "TIE_START",
    "TIE_STOP",
    "SLUR_START",
    "SLUR_STOP",
    "FERMATA",
    "HAIRPIN",
    "GRACE",
    "CHORD",
    "UNPITCHED",
]

_MUSICXML_EXTS = {".xml", ".musicxml", ".mxl"}
_MIDI_EXTS = {".mid", ".midi"}


def load(path) -> Work:
    """Parse a corpus source file into a Work, dispatching on extension
    (and zip magic for .mxl). Unknown formats fail loudly."""
    ext = os.path.splitext(str(path))[1].lower()
    if ext in _MUSICXML_EXTS:
        return load_musicxml(path)
    if ext in _MIDI_EXTS:
        return load_midi(path)
    raise IRParseError(f"{path}: unsupported source format {ext!r}")
