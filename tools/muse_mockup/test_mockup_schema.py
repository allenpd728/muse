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
    }


def test_valid_mockup_passes():
    assert validate_mockup_schema(_valid())


def test_provenance_seed_hash():
    m = _valid()
    m["provenance"] = {"seed_hash": "a" * 64}
    assert validate_mockup_schema(m)
    m["provenance"] = {"seed_hash": "sha256:" + "a" * 64}
    with pytest.raises(SchemaError, match="seed_hash"):
        validate_mockup_schema(m)
    m["provenance"] = {"seed_hash": "xyz"}
    with pytest.raises(SchemaError, match="seed_hash"):
        validate_mockup_schema(m)
    m["provenance"] = "not-a-dict"
    with pytest.raises(SchemaError, match="provenance"):
        validate_mockup_schema(m)


# --- L1.10 extended coverage (issue #257; spec
# tests/open_20260826-001500_l1-10-mockup-provenance.md) ---

GOOD_HASH = "b" * 64


def test_seed_hash_rejection_matrix():
    """short / long / non-hex / non-string all rejected."""
    for bad in ("b" * 63, "b" * 65, "h" * 64, 123, [GOOD_HASH]):
        m = _valid()
        m["provenance"] = {"seed_hash": bad}
        with pytest.raises(SchemaError, match="seed_hash"):
            validate_mockup_schema(m)


def test_seed_hash_accepts_both_hex_cases():
    """is_sha256_hex is case-insensitive, matching the manifest convention
    (pinned identically in test_manifest.py's parity matrix)."""
    for good in (GOOD_HASH, GOOD_HASH.upper(), "B0" * 32):
        m = _valid()
        m["provenance"] = {"seed_hash": good}
        assert validate_mockup_schema(m)


def test_provenance_additive_extra_keys():
    """Future run-metadata fields (run_id, provider, …) ride alongside
    seed_hash without tripping the validator — the typed-provider series
    must not be blocked here."""
    m = _valid()
    m["provenance"] = {"seed_hash": GOOD_HASH, "run_id": "r1", "provider": "gemini"}
    assert validate_mockup_schema(m)


def test_schema_pattern_parity_with_validator():
    """v1.json's regex pattern and is_sha256_hex agree on a shared matrix —
    the two enforcement layers must not drift."""
    import json as _json
    import re as _re
    from muse_seed.seed import is_sha256_hex

    pattern = _re.compile(
        _json.load(open(os.path.join(REPO, "tools", "muse_mockup", "schema", "v1.json")))
        ["properties"]["provenance"]["properties"]["seed_hash"]["pattern"]
    )
    matrix = [GOOD_HASH, GOOD_HASH.upper(), "b" * 63, "b" * 65, "h" * 64,
              "sha256:" + GOOD_HASH, "", "B0" * 32]
    for value in matrix:
        schema_ok = bool(pattern.fullmatch(value)) if isinstance(value, str) else False
        assert schema_ok == is_sha256_hex(value), (
            f"schema pattern vs is_sha256_hex disagree on {value!r}"
        )


def test_round_trip_seam_reports_dataclass_gap():
    """Spec item 1, pinned as the actual behavior: the Mockup dataclass
    does NOT carry provenance (dump/load silently drops it) — the schema
    field is for the session file on disk. If Mockup grows a provenance
    field later, this test must flip to assert the round-trip."""
    from muse_mockup import Mockup, Note, dump_mockup, load_mockup

    m = Mockup(work_id="x")
    m.notes = [Note(pitch=60, onset=0, duration=480, velocity=64, part="P1")]
    dumped = dump_mockup(m)
    assert "provenance" not in dumped, (
        "Mockup grew provenance serialization — flip this test to pin the round-trip"
    )
    back = load_mockup(dumped)
    assert not hasattr(back, "provenance") or getattr(back, "provenance", None) in (None, {})



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
    }
    assert validate_mockup_schema(adapted)
