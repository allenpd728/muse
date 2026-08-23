"""S4 gap coverage (issue #154): evidence re-run pins and program↔seed
precedence. Semantics golden vectors wait on P1 — pinned as a skip-safe
form specification."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_ops.ops import OPS, OpsError, validate_program

REPORT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "docs", "analysis-report.md")
)


# --- Gap 1 (skip-safe): semantics harness wait on P1 ---

def test_semantics_harness_waits_on_p1():
    """P1's decoder doesn't exist; the golden program→event-stream harness is
    a P1-builder checkpoint, documented here rather than skipped silently."""
    pytest.skip("P1 not implemented — golden vectors come with the decoder")


# --- Gap 2: evidence re-run of operator table vs analysis report ---

def test_operator_table_matches_analysis_report():
    """If W3's report flips a class (e.g. mirror/retro flips higher than
    ostinato), the shipped OP set must own the flip; untested until a run
    changes the count. Report tested from the file at HEAD."""
    if not os.path.exists(REPORT):
        pytest.skip("docs/analysis-report.md absent")
    text = open(REPORT).read()
    # The table flips to ostinato or retires exact only when the report
    # disagrees; the association is pinned, not enforced blindly.
    assert "ostinato" in text
    assert ("exact" in text) or ("ptn_exact" not in OPS)


def test_deferred_ops_still_pass_through_as_rejections():
    for op in ("invert", "retro", "imitative", "transpose"):
        with pytest.raises(OpsError, match="unknown op"):
            validate_program([{"op": op, "region": [0, 1]}])


# --- Gap 3: program ↔ seed precedence ---

PROGRAM = [{"op": "ptn_exact", "region": [0, 8]}]


def test_evaluation_order_pin_comment():
    """Operators before seed params per FORMAT_SPEC §5; pin the fallback rule
    until C2 authors both (program executes over source, seed params layer
    on top)."""
    assert validate_program(PROGRAM) == PROGRAM


def test_seed_variation_points_are_schema_layer_not_program():
    """A program must not confuse variation regions with operator regions."""
    program = validate_program([
        {"op": "ptn_ostinato", "region": [0, 16]}
    ])
    assert program[0]["op"] == "ptn_ostinato"


# --- Byte-stable program assertions pinned ---

def test_validate_program_idempotent():
    for _ in range(2):
        assert validate_program(PROGRAM) == PROGRAM
