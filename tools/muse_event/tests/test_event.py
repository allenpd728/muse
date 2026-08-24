"""E1 scaffold tests: ladder covered, chain callable, ledger shape."""

import json
import os

import pytest

from muse_event import LADDER, event_chain, run_ladder


def test_ladder_covers_corpus():
    rungs = [wid for _, _, wid in LADDER]
    assert rungs == ["BWV227.1", "Kyrie", "D.810", "Sym5 mvt1", "Sym9"]


def test_event_chain_ok(tmp_path):
    src = os.path.join("corpus", "bach", "bwv227.1.mxl")
    out_dir = str(tmp_path / "rung1")
    r = event_chain(src, "BWV227.1", 1, out_dir)
    assert r.found_working is True
    assert r.error == ""


def test_run_ladder_writes_ledger(tmp_path):
    out_root = str(tmp_path / "event")
    result = run_ladder(out_root)
    assert len(result["rungs"]) == 5
    assert all(r["ok"] for r in result["rungs"])
    ledger = json.load(open(os.path.join(out_root, "event-ledger.json")))
    assert ledger["event"] == "E1 ladder"
    assert len(ledger["rungs"]) == 5


def test_chain_ledger_shape(tmp_path):
    src = os.path.join("corpus", "beethoven", "beethoven-sym5-mov1.xml")
    out_dir = str(tmp_path / "rung")
    r = event_chain(src, "Sym5 mvt1", 4, out_dir)
    assert r.ledger["work_id"] == "Sym5 mvt1"
    assert r.ledger["rung"] == 4