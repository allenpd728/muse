"""E2E chain harness — corpus source → IR → roll → container → decode → render.

Each stage is a named function returning StageResult (PASS/FAIL/SKIP);
a failing stage isolates the owning task by name. P1 (sandboxed decoder)
and P2 (renderer) are stub stages until they land: the chain runs S2's
decode as the decoder stand-in and reports the stubs as SKIP.

Determinism: pack twice → identical roll bytes; artifacts are compared
as payloads (never zip container bytes, whose timestamps vary).
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field

from muse_ir import load
from muse_roll import decode as roll_decode
from muse_roll import encode as roll_encode
from muse_roll.roll import _canonical

CORPUS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "corpus"))

REGISTRY = [
    ("bach-bwv227.1", "bach/bwv227.1.mxl"),
    ("bach-bwv227.3", "bach/bwv227.3.mxl"),
    ("bach-bwv227.7", "bach/bwv227.7.mxl"),
    ("bach-bwv227.11", "bach/bwv227.11.mxl"),
    ("byrd-1-kyrie", "byrd/1-Kyrie.mid"),
    ("byrd-2-gloria", "byrd/2-Gloria.mid"),
    ("byrd-3-credo", "byrd/3-Credo.mid"),
    ("byrd-4-sanctus", "byrd/4-Sanctu.mid"),
    ("byrd-5-benedictus", "byrd/5-Bened.mid"),
    ("byrd-6-agnus", "byrd/6-Agnus.mid"),
    ("schubert-d810", "schubert/death-and-the-maiden.mxl"),
    ("beethoven-sym5-mov1", "beethoven/beethoven-sym5-mov1.xml"),
    ("beethoven-sym9", "beethoven/beethoven-sym9.xml"),
]

# W4 pairwise diff is quadratic; above this many events the chain proves
# losslessness structurally (canonical compare) instead.
DIFF_BUDGET_NOTES = 30000


@dataclass
class StageResult:
    stage: str           # stage name = owning task's noun
    status: str          # PASS | FAIL | SKIP
    detail: str = ""


@dataclass
class ChainResult:
    work_id: str
    relpath: str
    stages: list = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)  # name -> bytes

    @property
    def ok(self):
        return all(s.status != "FAIL" for s in self.stages)


def _stage_parse(work_id, relpath):
    work = load(os.path.join(CORPUS, relpath))
    return work, StageResult("parse(W1)", "PASS",
                             f"{len(work.parts)} parts, {work.note_count} notes")


def _stage_pack(work):
    a = roll_encode(work)
    b = roll_encode(work)
    if a != b:
        return None, StageResult("pack(S2)", "FAIL", "encode not deterministic")
    return a, StageResult("pack(S2)", "PASS", f"{len(a)} bytes, deterministic")


def _stage_container(work_id, relpath, roll_bytes, seed_bytes):
    from muse_mu import build_manifest, read_mu, write_mu

    prov = {"source": f"corpus/{relpath}", "author": "muse_chain",
            "ai_involvement": "none",
            "tools": ["tools/ir", "tools/muse_roll", "tools/muse_mu"]}
    lic = {"renditions": "closed",
           "attribution": "chain harness smoke artifact",
           "commercial": False}
    members = {"roll.bin": roll_bytes, "seed.bin": seed_bytes}
    manifest = build_manifest(work_id=work_id, license=lic, provenance=prov,
                              members=members)
    with tempfile.NamedTemporaryFile(suffix=".mu", delete=False) as tmp:
        path = tmp.name
    try:
        write_mu(path, manifest, members)
        back, got = read_mu(path)
    finally:
        os.unlink(path)
    if got != members:
        return None, StageResult("container(S5)", "FAIL",
                                 "member round-trip mismatch")
    return back.to_json().encode(), StageResult(
        "container(S5)", "PASS", "manifest verified, hashes match")


def _stage_decode(work, roll_bytes):
    rt = roll_decode(roll_bytes)
    if _canonical(rt) != _canonical(work):
        return StageResult("decode(P1-stub)", "FAIL",
                           "event stream mismatch after decode")
    return StageResult(
        "decode(P1-stub)", "PASS",
        "event stream identical (S2 decode stand-in; P1 sandboxed decoder pending)")


def _stage_diff(work, roll_bytes):
    if work.note_count > DIFF_BUDGET_NOTES:
        return StageResult("verify(W4)", "SKIP",
                           f"{work.note_count} notes > {DIFF_BUDGET_NOTES} budget; "
                           f"structural check already PASS")
    from muse_diff import diff

    report = diff(work, roll_decode(roll_bytes))
    if not report.ok():
        return StageResult("verify(W4)", "FAIL",
                           f"recall={report.recall:.4f} precision={report.precision:.4f}")
    return StageResult("verify(W4)", "PASS", "recall=precision=1.0")


def _stage_render():
    return StageResult("render(P2)", "SKIP", "renderer not yet implemented")


def run_work(work_id, relpath, seed_bytes=b"chain-seed-placeholder") -> ChainResult:
    result = ChainResult(work_id=work_id, relpath=relpath)
    try:
        work, s = _stage_parse(work_id, relpath)
    except Exception as e:
        result.stages.append(StageResult("parse(W1)", "FAIL",
                                         f"{type(e).__name__}: {e}"))
        return result
    result.stages.append(s)

    roll_bytes, s = _stage_pack(work)
    result.stages.append(s)
    if roll_bytes is None:
        return result
    result.artifacts["roll.bin"] = roll_bytes

    manifest_json, s = _stage_container(work_id, relpath, roll_bytes, seed_bytes)
    result.stages.append(s)
    if manifest_json is not None:
        result.artifacts["manifest.json"] = manifest_json

    result.stages.append(_stage_decode(work, roll_bytes))
    result.stages.append(_stage_diff(work, roll_bytes))
    result.stages.append(_stage_render())
    return result


def run_all(registry=REGISTRY):
    return [run_work(wid, rel) for wid, rel in registry]


def check_determinism(registry=REGISTRY):
    """Two full runs → identical artifacts per work; failures listed."""
    first = {r.work_id: r.artifacts for r in run_all(registry)}
    second = {r.work_id: r.artifacts for r in run_all(registry)}
    mismatches = []
    for wid in first:
        for name, blob in first[wid].items():
            if second[wid].get(name) != blob:
                mismatches.append(f"{wid}:{name}")
    return mismatches
