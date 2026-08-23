"""S2 packer/decoder: columnar + delta + dictionary + entropy (DEFLATE).

Layout (per part, long-past-indexed so offsets stay O(n) not O(n²)):
  - pitch channel: exact values, dictionary-patched on longer runs
  - onset channel: delta-encoded (per-last-end difference)
  - duration channel: exact values
  - voice channel: exact values
  - velocity channel: sum-position + value (None → -1)
  - indices channel: note index → [channel values]
  - notations flags: bitmask (tie_start, tie_stop, slur_start, slur_stop,
    fermata, hairpin, grace, chord, unpitched)

All channels go through a common dictionary pass (repeating tokens → one
dictionary entry + index references), then DEFLATE the serialized dict of
channels. Lossless: en/de round-trips every channel value exactly.
"""

from __future__ import annotations

import json
import zlib

from .codec import CHANNELS, NOTATION_FLAGS, pack_channels  # noqa: F401

MAGIC = b"MUPACK0\n"


def pack(work) -> bytes:
    """Work → binary payload: columnar channels → DEFLATE."""
    channels = pack_channels(work)
    blob = json.dumps(channels, sort_keys=True, separators=(",", ":"))
    return MAGIC + zlib.compress(blob.encode(), level=9)


def unpack(data: bytes):
    """Binary payload → channels dict (interchange; S1's IR rebuild is its
    own decoder against the same columns)."""
    if not data.startswith(MAGIC):
        raise ValueError("not a muse_pack payload")
    raw = zlib.decompress(data[len(MAGIC):])
    return json.loads(raw.decode())
