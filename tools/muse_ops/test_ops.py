"""S4 language validator tests (issue #140).

Grammar pins for the three shipped operators; deferred operators rejected;
bounds and example programs.
"""

import pytest

from muse_ops import OPS, OpsError, validate_program


def entry(op="ptn_exact", **kw):
    d = {"op": op, "region": [0, 480]}
    d.update(kw)
    return d


class TestShippedOperators:
    def test_all_three_ship(self):
        assert OPS == {"ptn_exact", "ptn_transposed", "ptn_ostinato"}

    def test_deferred_operators_rejected(self):
        for op in ("ptn_invert", "ptn_retro", "ptn_imitative", "transpose"):
            with pytest.raises(OpsError, match="unknown op"):
                validate_program([entry(op=op)])

    def test_empty_program_valid(self):
        assert validate_program([]) == []

    def test_program_must_be_list(self):
        with pytest.raises(OpsError, match="must be a list"):
            validate_program({"op": "ptn_exact"})


class TestEntryGrammar:
    def test_unknown_keys_rejected(self):
        with pytest.raises(OpsError, match="unknown keys"):
            validate_program([entry(vibe="loose")])

    def test_region_shape(self):
        for bad in ([0], [0, 480, 960], "0-480", [0.0, 480.0], None):
            with pytest.raises(OpsError, match="region"):
                validate_program([entry(region=bad)])

    def test_empty_region_rejected(self):
        with pytest.raises(OpsError, match="empty/negative"):
            validate_program([entry(region=[480, 480])])
        with pytest.raises(OpsError, match="empty/negative"):
            validate_program([entry(region=[-1, 480])])

    def test_transposed_requires_signed_interval(self):
        validate_program([entry(op="ptn_transposed", interval="+2")])
        validate_program([entry(op="ptn_transposed", interval="-5")])
        for bad in ("2", "+", 2, None, "+x"):
            with pytest.raises(OpsError, match="interval"):
                validate_program([entry(op="ptn_transposed", interval=bad)])

    def test_exact_ostinato_forbid_no_interval(self):
        # interval key is permitted by the schema but only meaningful on
        # ptn_transposed; pins that ptn_exact/ostinato without interval pass
        validate_program([entry(op="ptn_exact")])
        validate_program([entry(op="ptn_ostinato")])

    def test_part_must_be_string(self):
        validate_program([entry(part="P2")])
        with pytest.raises(OpsError, match="part"):
            validate_program([entry(part=2)])

    def test_error_message_indexes_entry(self):
        with pytest.raises(OpsError, match=r"program\[1\]"):
            validate_program([entry(), entry(op="bogus")])


class TestBounds:
    def test_region_outside_work_rejected(self):
        with pytest.raises(OpsError, match="exceeds work duration"):
            validate_program([entry(region=[0, 1000])], duration_ticks=960)

    def test_region_inside_work_accepted(self):
        validate_program([entry(region=[0, 960])], duration_ticks=960)

    def test_no_work_no_bounds_check(self):
        validate_program([entry(region=[0, 10**9])])


class TestExamplePrograms:
    """Hand-written example programs exercising each shipped construct
    (the spec's acceptance criterion)."""

    def test_bach_chorale_program(self):
        program = [
            {"op": "ptn_exact", "region": [0, 768], "part": "P1"},
            {"op": "ptn_transposed", "region": [768, 1536], "interval": "+2", "part": "P2"},
            {"op": "ptn_ostinato", "region": [0, 1536], "part": "P4"},
        ]
        assert validate_program(program, duration_ticks=1536) == program

    def test_byrd_imitation_as_transposed(self):
        # Byrd's point-of-imitation entries model as transposed repeats
        program = [
            {"op": "ptn_transposed", "region": [0, 1920], "interval": "-4", "part": "T1"},
            {"op": "ptn_transposed", "region": [1920, 3840], "interval": "+0", "part": "T2"},
        ]
        validate_program(program)

    def test_schubert_ostinato_layer(self):
        program = [
            {"op": "ptn_ostinato", "region": [0, 9600], "part": "P4"},
            {"op": "ptn_exact", "region": [9600, 19200]},
        ]
        validate_program(program)
