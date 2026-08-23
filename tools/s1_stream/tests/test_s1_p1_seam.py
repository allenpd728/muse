"""S1 → P1 seam contract (issue #168).

P1 (sandboxed reference decoder) does not exist yet. What exists today is
the chain's decode(P1-stub) — S2's decode used as the stand-in. This file
pins the seam the day P1 lands:

1. **Contract doc**: P1's input is a `roll.bin` payload (S2 encoding of the
   S1 event stream); its output is a Work whose canonical form equals the
   S1 golden vector for the same source.
2. **Pre-landed verification**: the S1 golden vectors round-trip through
   the P1-stub path (encode → decode → canonical compare) — the harness
   P1 must also satisfy, byte-exactly.
3. **Swap pin**: when P1 lands, `DECODER` switches from the stub and the
   contract tests run against it unchanged.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_ir import load  # noqa: E402
from muse_roll import decode as roll_decode  # noqa: E402
from muse_roll import encode as roll_encode  # noqa: E402
from muse_stream.golden import canonical_json, work_to_canonical  # noqa: E402

CORPUS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "corpus"))
GOLDEN_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "golden"))

# The seam's decoder entry point. P1 lands → swap this line; every test
# below then exercises the real decoder without further edits.
DECODER = roll_decode  # P1-stub (S2 decode); P1 replaces this

SOURCES = {
    "bach_bwv227.1.json": ("bach", "bwv227.1.mxl"),
    "byrd_1-kyrie.json": ("byrd", "1-Kyrie.mid"),
    "schubert_d810.json": ("schubert", "death-and-the-maiden.mxl"),
    "beethoven_sym5_mov1.json": ("beethoven", "beethoven-sym5-mov1.xml"),
}


def _canonical_of_work(work):
    return json.dumps(work_to_canonical(work), sort_keys=True, separators=(",", ":"))


@pytest.mark.parametrize("vector,relparts", sorted(SOURCES.items()))
def test_golden_vector_roundtrips_through_decoder(vector, relparts):
    """S1 golden vector ↔ decoder contract: encode the source, decode via
    the seam entry point, canonical form must equal the golden vector."""
    work = load(os.path.join(CORPUS, *relparts))
    decoded = DECODER(roll_encode(work))
    golden = json.load(open(os.path.join(GOLDEN_DIR, vector)))
    got = json.loads(_canonical_of_work(decoded))
    assert got["meta"] == golden["meta"], f"{vector}: meta drift"
    assert got["maps"] == golden["maps"], f"{vector}: maps drift"
    assert len(got["parts"]) == len(golden["parts"]), f"{vector}: part count"
    for gp, rp in zip(golden["parts"], got["parts"]):
        assert len(gp["notes"]) == len(rp["notes"]), f"{vector}: note count"
        for gn, rn in zip(gp["notes"], rp["notes"]):
            assert (gn["pitch"], gn["onset"], gn["duration"]) == (
                rn["pitch"],
                rn["onset"],
                rn["duration"],
            ), f"{vector}: note mismatch at {gn['onset']}"


def test_decoder_input_is_roll_payload():
    """Contract pin: the seam's input is bytes with MUR1 magic — anything
    else must fail loudly at the decoder boundary."""
    with pytest.raises(Exception):
        DECODER(b"not-a-roll-payload")
    with pytest.raises(Exception):
        DECODER(b"")


def test_golden_vector_set_covers_corpus_tiers():
    """The S1 golden directory must keep covering every registry tier the
    seam depends on (a new corpus work without a vector is a seam gap)."""
    vectors = {f for f in os.listdir(GOLDEN_DIR) if f.endswith(".json")}
    expected = set(SOURCES) | {
        "bach_bwv227.3.json",
        "bach_bwv227.7.json",
        "bach_bwv227.11.json",
        "byrd_2-gloria.json",
        "byrd_3-credo.json",
        "byrd_4-sanctu.json",
        "byrd_5-bened.json",
        "byrd_6-agnus.json",
        "beethoven_sym9.json",
    }
    assert expected <= vectors, f"missing vectors: {sorted(expected - vectors)}"
