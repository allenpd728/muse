"""E1 scaffold tests: ladder covered, chain callable, ledger shape."""

import json
import os

import pytest

from muse_event import LADDER, event_chain, run_ladder

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def corpus_path(*parts):
    return os.path.join(REPO, "corpus", *parts)


def test_ladder_covers_corpus():
    rungs = [wid for _, _, wid in LADDER]
    assert rungs == ["BWV227.1", "Kyrie", "D.810", "Sym5 mvt1", "Sym9"]


def test_event_chain_ok(tmp_path):
    src = corpus_path("bach", "bwv227.1.mxl")
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
    src = corpus_path("beethoven", "beethoven-sym5-mov1.xml")
    out_dir = str(tmp_path / "rung")
    r = event_chain(src, "Sym5 mvt1", 4, out_dir)
    assert r.ledger["work_id"] == "Sym5 mvt1"
    assert r.ledger["rung"] == 4


# --- Gap 2 (issue #226): missing corpus sources fail the rung gracefully,
# with details, and don't take down the ladder. ---

def test_missing_source_fails_rung_with_detail(tmp_path):
    r = event_chain("corpus/bach/no-such-file.mxl", "BWV227.1", 1,
                    str(tmp_path / "rung"))
    assert r.found_working is False
    assert "no-such-file.mxl" in r.error


def test_ladder_continues_past_missing_rung(tmp_path, monkeypatch):
    ladder = list(LADDER)
    ladder[1] = ("byrd", "missing.mid", "Kyrie")
    monkeypatch.setattr("muse_event.event.LADDER", ladder)
    result = run_ladder(str(tmp_path / "event"))
    assert len(result["rungs"]) == 5
    kyrie = next(r for r in result["rungs"] if r["work_id"] == "Kyrie")
    assert kyrie["ok"] is False
    assert "missing.mid" in kyrie["error"]
    assert all(r["ok"] for r in result["rungs"] if r["work_id"] != "Kyrie")


# --- Gap 4 (issue #226): the ledger is written once, at completion. ---

def test_ledger_written_on_completion_only(tmp_path):
    out_root = str(tmp_path / "event")
    assert not os.path.exists(os.path.join(out_root, "event-ledger.json"))
    run_ladder(out_root)
    assert os.path.exists(os.path.join(out_root, "event-ledger.json"))