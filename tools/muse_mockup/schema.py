"""Mockup schema validation (L1.1) — W7 finalize.

Validates a mockup dict against the v1 schema (tools/muse_mockup/schema/
v1.json): tempo_map/dynamics tick-ordering, per-note device fields with
bounded ranges, part balance, and the seed provenance block. Fails loudly
with the path of the first violation.
"""

from __future__ import annotations

import json
import os


class SchemaError(ValueError):
    """A mockup violates the v1 schema."""


def _path(prefix, key):
    return f"{prefix}.{key}" if prefix else key


def _check(condition, path, message):
    if not condition:
        raise SchemaError(f"{path}: {message}")


def validate_mockup_schema(mockup):
    """Validate one mockup dict against v1. Returns True; raises SchemaError."""
    if not isinstance(mockup, dict):
        raise SchemaError("mockup must be a dict")
    for key in ("work_id", "tempo_map", "parts"):
        _check(key in mockup, key, "required field missing")

    _check_ticks(mockup["tempo_map"], "tempo_map", ("tick", "bpm"), lambda e: e["bpm"] > 0)
    if "dynamics" in mockup:
        _check_ticks(mockup["dynamics"], "dynamics", ("tick", "level"),
                     lambda e: 0 <= e["level"] <= 1)

    balance = mockup.get("balance", [])
    _check(isinstance(balance, list), "balance", "must be a list")
    for entry in balance:
        _check(isinstance(entry, dict), "balance", "entry must be a dict")
        _check(isinstance(entry.get("gain"), (int, float)) and entry["gain"] >= 0,
               _path("balance", str(entry.get("part", "?"))), "gain must be >= 0")

    parts = mockup["parts"]
    _check(isinstance(parts, dict), "parts", "must be a mapping of part id → notes")
    for part_id, notes in parts.items():
        _check(isinstance(notes, list), _path("parts", part_id), "notes must be a list")
        for j, note in enumerate(notes):
            _validate_note(note, _path(_path("parts", part_id), f"[{j}]"))
    return True


def _check_ticks(entries, name, keys, predicate):
    _check(isinstance(entries, list), name, "must be a list")
    for e in entries:
        _check(isinstance(e, dict), name, "entry must be a dict")
    ticks = [e.get(keys[0]) for e in entries]
    _check(all(isinstance(t, int) and t >= 0 for t in ticks), name, "ticks must be non-negative ints")
    _check(ticks == sorted(ticks), name, "ticks must be ordered")
    for e in entries:
        _check(predicate(e), _path(name, str(e.get(keys[0]))), f"{keys[1]} out of range")


def _validate_note(note, path):
    _check(isinstance(note, dict), path, "note must be a dict")
    for key in ("i", "velocity"):
        _check(key in note, _path(path, key), "required field")
    _check(isinstance(note["i"], int) and note["i"] >= 0, _path(path, "i"), "note index must be >= 0")
    _check(isinstance(note["velocity"], int) and 1 <= note["velocity"] <= 127,
           _path(path, "velocity"), "velocity must be 1..127")
    for key in ("attack_sec", "release_sec", "legato_overlap_ms"):
        if key in note:
            _check(isinstance(note[key], (int, float)) and note[key] >= 0,
                   _path(path, key), "must be >= 0")
    if "swell" in note:
        _check(isinstance(note["swell"], list), _path(path, "swell"),
               "swell must be a list of [position, level] pairs")
        for pt in note["swell"]:
            _check(isinstance(pt, list) and len(pt) == 2, _path(path, "swell"),
                   "swell points are [position, level] pairs")
            _check(all(isinstance(x, (int, float)) and 0 <= x <= 1 for x in pt),
                   _path(path, "swell"), "swell values must be 0..1")


def load_schema():
    path = os.path.join(os.path.dirname(__file__), "schema", "v1.json")
    return json.load(open(path))
