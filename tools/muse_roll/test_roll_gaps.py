"""Tests: S2 follow-up (issue #170) — B9 budget pin, golden roll vectors,
format-version tripwire, size regression budget.

Spec: tests/open_20260823-212500_s2-roll-encoding.md → closed with this file.
"""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))

from muse_ir import load  # noqa: E402
from muse_roll.roll import MAGIC, decode, encode  # noqa: E402

CORPUS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "corpus"))
FIXTURES = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "tests", "fixtures"))


# --- Gap 1: B9 W4 verify budget (slow tier) ---

@pytest.mark.slow
def test_beethoven9_roundtrip_budget():
    """B9 (239k notes) round-trips structurally within a pinned budget.

    Encode+decode must stay cheap (<30s); part note counts are the
    structural equality check (W4's pairwise diff on 239k events is the
    out-of-band verify, pinned here as the budget record).
    """
    work = load(os.path.join(CORPUS, "beethoven", "beethoven-sym9.xml"))
    t0 = time.time()
    payload = encode(work)
    t1 = time.time()
    restored = decode(payload)
    t2 = time.time()
    assert t1 - t0 < 30, f"encode took {t1 - t0:.1f}s (budget 30s)"
    assert t2 - t1 < 30, f"decode took {t2 - t1:.1f}s (budget 30s)"
    assert [len(p.notes) for p in restored.parts] == [
        len(p.notes) for p in work.parts
    ]
    assert len(payload) == 168281  # measured 2026-08-23; drift is a review


# --- Gap 2: golden roll vectors ---

GOLDEN = {
    "bwv227.1.roll.bin": ("bach", "bwv227.1.mxl"),
    "byrd-kyrie.roll.bin": ("byrd", "1-Kyrie.mid"),
}


@pytest.mark.parametrize("fixture,source", sorted(GOLDEN.items()))
def test_golden_roll_byte_exact(fixture, source):
    """Format drift fails byte-exact: regenerate and compare."""
    work = load(os.path.join(CORPUS, *source))
    golden = open(os.path.join(FIXTURES, fixture), "rb").read()
    regenerated = encode(work)
    assert regenerated == golden, (
        f"{fixture}: payload drifted from golden "
        f"({len(regenerated)} vs {len(golden)} bytes) — intended format "
        f"change? bump R-version and regenerate per docs."
    )


def test_golden_roll_decodes_lossless():
    """Golden payloads decode to the same note stream as the source."""
    work = load(os.path.join(CORPUS, "bach", "bwv227.1.mxl"))
    golden = open(os.path.join(FIXTURES, "bwv227.1.roll.bin"), "rb").read()
    restored = decode(golden)
    assert [len(p.notes) for p in restored.parts] == [
        len(p.notes) for p in work.parts
    ]
    for a, b in zip(work.parts, restored.parts):
        for na, nb in zip(a.notes, b.notes):
            assert (na.pitch, na.onset, na.duration) == (
                nb.pitch,
                nb.onset,
                nb.duration,
            )


# --- Gap 3: format-version tripwire ---

def test_magic_is_r1_tripwire():
    """MUR1 is the pinned v1 magic. A v2 bump must change this test and the
    compat posture in the same commit."""
    assert MAGIC == b"MUR1"
    work = load(os.path.join(CORPUS, "bach", "bwv227.1.mxl"))
    assert encode(work).startswith(b"MUR1")


def test_decode_rejects_future_version():
    """Unknown magic (e.g. a future MUR2 read by an old decoder) fails
    loudly, never partially."""
    work = load(os.path.join(CORPUS, "bach", "bwv227.1.mxl"))
    payload = bytearray(encode(work))
    payload[3] = ord("2")
    with pytest.raises(Exception):
        decode(bytes(payload))


# --- Gap 4: size regression budget ---

SIZE_BUDGET = {
    ("bach", "bwv227.1.mxl"): 0.15,  # measured 0.104
    ("byrd", "1-Kyrie.mid"): 0.25,  # measured 0.177
    ("schubert", "death-and-the-maiden.mxl"): 0.15,  # measured 0.096
    ("beethoven", "beethoven-sym5-mov1.xml"): 0.01,  # measured 0.0026
}


@pytest.mark.parametrize("relparts", sorted(SIZE_BUDGET))
def test_size_regression_budget(relparts):
    """Packed size must stay under the pinned ratio ceiling."""
    ceiling = SIZE_BUDGET[relparts]
    src = os.path.join(CORPUS, *relparts)
    payload = encode(load(src))
    ratio = len(payload) / os.path.getsize(src)
    assert ratio <= ceiling, (
        f"{'/'.join(relparts)}: ratio {ratio:.4f} exceeds budget {ceiling}"
    )
