"""Mockup schema v1 tests (issue #206)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_mockup.schema import SchemaError, validate_mockup_schema  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _valid():
    return {
        "work_id": "x",
        "tempo_map": [{"tick": 0, "bpm": 96.0}, {"tick": 100, "bpm": 90.0}],
        "dynamics": [{"tick": 0, "level": 0.5}, {"tick": 100, "level": 0.8}],
        "balance": [{"part": "P1", "gain": 1.0}],
        "parts": {"P1": [{"i": 0, "velocity": 64, "attack_sec": 0.05,
                          "swell": [[0, 0.5], [1, 0.9]]}]},
        "seed": {},
    }


def test_valid_mockup_passes():
    assert validate_mockup_schema(_valid())


def test_missing_required_field():
    with pytest.raises(SchemaError, match="required field"):
        validate_mockup_schema({"work_id": "x"})


def test_unordered_ticks_rejected():
    m = _valid()
    m["tempo_map"] = [{"tick": 10, "bpm": 90}, {"tick": 5, "bpm": 90}]
    with pytest.raises(SchemaError, match="ordered"):
        validate_mockup_schema(m)


def test_bpm_zero_rejected():
    m = _valid()
    m["tempo_map"][0]["bpm"] = 0
    with pytest.raises(SchemaError, match="bpm"):
        validate_mockup_schema(m)


def test_velocity_out_of_range_rejected():
    m = _valid()
    m["parts"]["P1"][0]["velocity"] = 200
    with pytest.raises(SchemaError, match="velocity"):
        validate_mockup_schema(m)


def test_swell_out_of_range_rejected():
    m = _valid()
    m["parts"]["P1"][0]["swell"] = [[0, 2]]
    with pytest.raises(SchemaError, match="swell"):
        validate_mockup_schema(m)


def test_spike_mockup_v3_adapts_and_validates():
    """The spike's richest mockup (v3) adapts to v1 shape and validates —
    the evidence base for the schema."""
    d = json.load(open(os.path.join(REPO, "docs", "spike", "mockup-v3.json")))
    adapted = {
        "work_id": "byrd-kyrie",
        "tempo_map": [{"tick": e["tick"], "bpm": e["bpm"]} for e in d["tempo_map"]],
        "dynamics": [{"tick": e["tick"], "level": e["level"]} for e in d["dynamics"]],
        "balance": d["balance"],
        "parts": d["notes"],
        "seed": d["seed"],
    }
    assert validate_mockup_schema(adapted)
