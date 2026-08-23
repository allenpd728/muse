"""Muse event-stream IR (W1).

Canonical in-memory representation every tool shares. Integer ticks only.
Parsers: MusicXML (.xml/.mxl) and MIDI (.mid) via partitura + mido.
"""

from .model import Work, Part, Note, ValidationError
from .parse import load, load_musicxml, load_midi

__all__ = [
    "Work",
    "Part",
    "Note",
    "ValidationError",
    "load",
    "load_musicxml",
    "load_midi",
]
