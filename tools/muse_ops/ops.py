"""S4 language validator — grammar-only checks for .mu programs.

The three shipped operators (W3 evidence, FORMAT_SPEC §5.1): ptn_exact,
ptn_transposed, ptn_ostinato. Invert/retro/imitative deferred — no corpus
evidence. This validator checks grammar + region bounds; semantics are
P1's decoder.
"""

from __future__ import annotations

import re


class OpsError(ValueError):
    """Raised when a program violates the S4 grammar."""


OPS = frozenset({"ptn_exact", "ptn_transposed", "ptn_ostinato"})
INTERVAL_OPS = frozenset({"ptn_transposed"})
_INTERVAL_RE = re.compile(r"^[+-]\d+$")


def validate_program(program: list, duration_ticks=None):
    """Validate a program (list of operator entries). Returns the entries."""
    if not isinstance(program, list):
        raise OpsError("program must be a list")
    for i, entry in enumerate(program):
        _validate_entry(i, entry)
    for entry in program:
        _check_bounds(entry, duration_ticks)
    return program


def _validate_entry(index, entry):
    if not isinstance(entry, dict):
        raise OpsError(f"program[{index}]: entry must be a mapping")
    unknown = set(entry) - {"op", "region", "part", "interval"}
    if unknown:
        raise OpsError(f"program[{index}]: unknown keys {sorted(unknown)}")
    op = entry.get("op")
    if op not in OPS:
        raise OpsError(
            f"program[{index}]: unknown op {op!r} (shipped: {sorted(OPS)})")
    region = entry.get("region")
    if (not isinstance(region, list) or len(region) != 2
            or not all(isinstance(t, int) for t in region)):
        raise OpsError(f"program[{index}]: region must be [start, end] ints")
    if region[0] < 0 or region[1] <= region[0]:
        raise OpsError(f"program[{index}]: empty/negative region {region}")
    if op in INTERVAL_OPS:
        interval = entry.get("interval")
        if not isinstance(interval, str) or not _INTERVAL_RE.match(interval):
            raise OpsError(
                f"program[{index}]: ptn_transposed needs interval as signed "
                f"string ('+2', '-5')")
    if "part" in entry and not isinstance(entry["part"], str):
        raise OpsError(f"program[{index}]: part must be a part id string")


def _check_bounds(entry, duration_ticks):
    if duration_ticks is None:
        return
    region = entry["region"]
    if region[1] > duration_ticks:
        raise OpsError(
            f"region {region} exceeds work duration {duration_ticks}")
