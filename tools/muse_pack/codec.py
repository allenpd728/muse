"""Column extraction and dictionary pass shared by packer/decoder.

Channels per part, note-indexed (position i = the IR's sorted note i):
  - pitch: -1 for rests/unpitched, else 0..127
  - onset_delta: onset[i] - (onset[i-1] + duration[i-1]) — absolute recovery
  - duration: source ticks (>0 for non-grace, 0 for grace)
  - voice: -1 for None, else >=1
  - velocity: -1 for None, else 0..127
  - notations: bitmask per note over the flag vocabulary

Each channel goes through a dictionary pass (repeating blocks >= _DICT_MIN
tokens → entry ids) before JSON serialization; DEFLATE handles entropy.
Everything round-trips exactly per W4's diff.
"""

from __future__ import annotations

CHANNELS = (
    "pitch",
    "onset_delta",
    "duration",
    "voice",
    "velocity",
    "articulations",
    "notations",
)

NOTATION_FLAGS = (
    "tie_start",
    "tie_stop",
    "slur_start",
    "slur_stop",
    "fermata",
    "hairpin",
    "grace",
    "chord",
    "unpitched",
)

from .vocab import articulations_to_bits

_FLAG_BITS = {name: 1 << i for i, name in enumerate(NOTATION_FLAGS)}
_DICT_MIN = 4


def pack_channels(work):
    """Work → channels dict. Deterministic under the IR's note ordering."""
    return {
        "s2_version": 0,
        "meta": {
            "source_format": work.meta.source_format,
            "ppq": work.meta.ppq,
            "title": work.meta.title,
            "warnings": sorted(work.meta.warnings),
        },
        "maps": {
            "tempo": [[t, mb] for t, mb in work.maps.tempo],
            "meter": [[t, n, d] for t, n, d in work.maps.meter],
            "key": [[t, f, m] for t, f, m in work.maps.key],
        },
        "parts": [_part_channels(p) for p in work.parts],
    }


def _part_channels(part):
    pitch, onset_delta, duration, voice, velocity, notations, articulations = (
        [] for _ in range(7)
    )
    prev_end = 0
    for n in part.notes:
        pitch.append(-1 if n.pitch is None else n.pitch)
        onset_delta.append(n.onset - prev_end)
        prev_end += onset_delta[-1] + n.duration
        duration.append(n.duration)
        voice.append(-1 if n.voice is None else n.voice)
        velocity.append(-1 if n.velocity is None else n.velocity)
        notations.append(
            sum(1 << NOTATION_FLAGS.index(f) for f in n.notations if f in NOTATION_FLAGS)
        )
        articulations.append(articulations_to_bits(n.articulations))
    return {
        "id": part.id,
        "name": part.name,
        "instrument": {
            "name": part.instrument.name,
            "gm_program": part.instrument.gm_program,
        },
        "inferred_voice": part.inferred_voice,
        "dynamics": [[d.tick, d.text] for d in part.dynamics],
        "hairpins": [[h.kind, h.start_tick, h.end_tick] for h in part.hairpins],
        "pitch": _encode(pitch),
        "onset_delta": _encode(onset_delta),
        "duration": _encode(duration),
        "voice": _encode(voice),
        "velocity": _encode(velocity),
        "notations": _encode(notations),
        "articulations": _encode(articulations),
        "note_count": len(part.notes),
    }


def _encode(values):
    """Channel→terminal-coded form. v0 keeps literals verbatim; the packer's
    entropy layer is zlib. A dictionary pass is explicitly not v0 — the
    pattern inventory lives at the W3 layer; here, exactness first."""
    return {"dict": [], "coded": [["v", v] for v in values]}


def decode_channel(channel):
    """Revert one channel to its values (encode's exact inverse)."""
    dict_id = {i: tuple(v) for i, v in enumerate(channel["dict"])}
    values = []
    for item in channel["coded"]:
        if item[0] == "v":
            values.append(item[1])
        elif item[0] == "t":  # registered dictionary entry announcement
            dict_id[item[1]] = tuple(item[2])
            # tokens are announced but not emitted until referenced
        elif item[0] == "d":
            block = dict_id[item[1]]
            values.extend(block[: item[2]])
    return values
