"""S1 golden-vector tests: canonical form determinism, verify round-trip,
and conformance pins on generated vectors."""

import json
import os

import pytest

from muse_ir import load
from muse_stream import canonical_json, verify, work_to_canonical

from conftest import corpus_path


def test_canonical_form_is_deterministic():
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    a = canonical_json(work)
    b = canonical_json(load(corpus_path("bach", "bwv227.1.mxl")))
    assert a == b
    assert a.endswith("\n")
    # canonical separators: no whitespace
    assert '", "' not in a and '": ' not in a


def test_work_to_canonical_structure():
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    doc = work_to_canonical(work)
    assert doc["s1_version"] == 0
    assert doc["meta"]["source_format"] == "musicxml"
    assert doc["meta"]["ppq"] == 2
    assert len(doc["parts"]) == 4
    total = sum(len(p["notes"]) for p in doc["parts"])
    assert total == 279
    assert doc["maps"]["tempo"] == [[0, 96000]]
    first = doc["parts"][0]["notes"][0]
    assert first["pitch"] == 71 and first["onset"] == 0 and first["duration"] == 2


def test_verify_round_trip(tmp_path):
    src = corpus_path("byrd", "1-Kyrie.mid")
    vector = tmp_path / "kyrie.json"
    vector.write_text(canonical_json(load(src)))
    assert verify(src, str(vector))


def test_verify_detects_tampering(tmp_path):
    src = corpus_path("bach", "bwv227.1.mxl")
    doc = work_to_canonical(load(src))
    doc["parts"][0]["notes"][0]["pitch"] = 99
    vector = tmp_path / "tampered.json"
    vector.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n")
    assert not verify(src, str(vector))


def test_dynamics_and_hairpins_serialize():
    work = load(corpus_path("beethoven", "beethoven-sym5-mov1.xml"))
    doc = work_to_canonical(work)
    dyn = sum(len(p["dynamics"]) for p in doc["parts"])
    assert dyn == 431
    notes_with_notations = sum(
        1 for p in doc["parts"] for n in p["notes"] if n["notations"]
    )
    assert notes_with_notations > 0


def test_unpitched_preserved_in_vector():
    work = load(corpus_path("beethoven", "beethoven-sym9.xml"))
    doc = work_to_canonical(work)
    unpitched = sum(1 for p in doc["parts"] for n in p["notes"] if n["unpitched"])
    assert unpitched == 835
