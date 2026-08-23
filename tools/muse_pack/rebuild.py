"""Unpack channels → canonical S1-shaped dict (sorted notes per part).

The decoder contract: payload → canonical dict identical to the S1 golden
dump at every note position. The W4 diff then proves the round-trip lossless.
"""

from __future__ import annotations

from .codec import NOTATION_FLAGS, decode_channel
from .vocab import bits_to_articulations


def unpack_to_canonical(payload):
    """Channels dict → canonical form matching S1's golden dump shape."""
    parts = []
    for part in payload["parts"]:
        onsets = _reconstruct_onsets(part)
        notes = []
        articulations_values = decode_channel(part["articulations"])
        for i in range(part["note_count"]):
            pitch_values = decode_channel(part["pitch"])
            voice_values = decode_channel(part["voice"])
            velocity_values = decode_channel(part["velocity"])
            notations_values = decode_channel(part["notations"])
            pitch = pitch_values[i] if pitch_values[i] != -1 else None
            notes.append(
                {
                    "pitch": pitch,
                    "onset": onsets[i],
                    "duration": decode_channel(part["duration"])[i],
                    "voice": voice_values[i] if voice_values[i] != -1 else None,
                    "velocity": (
                        velocity_values[i] if velocity_values[i] != -1 else None
                    ),
                    "velocity_inferred": False,
                    "articulations": bits_to_articulations(articulations_values[i]),
                    "notations": _flags(notations_values[i]),
                    "unpitched": "unpitched" in _flags(notations_values[i]),
                }
            )
        notes.sort(key=lambda n: (n["onset"], -1 if n["pitch"] is None else n["pitch"]))
        parts.append(
            {
                "id": part["id"],
                "name": part["name"],
                "instrument": part["instrument"],
                "inferred_voice": part["inferred_voice"],
                "dynamics": part["dynamics"],
                "hairpins": part["hairpins"],
                "notes": notes,
            }
        )
    return {
        "s1_version": 0,
        "meta": payload["meta"],
        "maps": payload["maps"],
        "parts": parts,
    }


def _reconstruct_onsets(part):
    """Absolute onsets = cumulative onset_delta + cumulative duration."""
    deltas = decode_channel(part["onset_delta"])
    durations = decode_channel(part["duration"])
    onsets = []
    prev_end = 0
    for i in range(part["note_count"]):
        onsets.append(prev_end + deltas[i])
        prev_end = onsets[-1] + durations[i]
    return onsets


def _flags(bits):
    return sorted(f for i, f in enumerate(NOTATION_FLAGS) if bits & (1 << i))
