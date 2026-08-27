"""ManualProvider spike (L1.11 #276 founder decision): the conversation-as-model
path produces a real, non-flat, full-coverage mockup through the L1 loop.

The ManualProvider is driven by a prepared mockup (the "paste" an OpenHands
conversation would produce); generate_mockup validates it; the distiller
confirms the interpretation is non-flat where the stand-in is flat. The
committed expressive mockup is the recorded fixture.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_ir import load as load_work  # noqa: E402
from muse_seed import load_seed  # noqa: E402
from muse_generate import generate_mockup  # noqa: E402
from muse_provider import ManualProvider  # noqa: E402
from muse_mockup import load_mockup  # noqa: E402
from muse_distill import extract_interpretation  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WORK = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")
SEED = os.path.join(REPO, "seeds", "bwv227.1.v2.seed.yaml")
EXPRESSIVE = os.path.join(REPO, "seeds", "bwv227.1.v2.expressive.mockup.json")


def test_manual_provider_validates_full_coverage_mockup():
    work = load_work(WORK)
    seed = load_seed(open(SEED).read(), fmt="yaml")
    # ManualProvider pastes the session-shape (schema v1) JSON the
    # conversation produced. Build it from the committed dump-shape
    # expressive mockup: parts = {part_id: [{i, velocity}]}.
    dump = json.load(open(EXPRESSIVE))
    parts = {}
    counters = {}
    for n in dump["notes"]:
        i = counters.get(n["part"], 0)
        counters[n["part"]] = i + 1
        parts.setdefault(n["part"], []).append({"i": i, "velocity": n["velocity"]})
    session_v1 = {
        "work_id": dump["work_id"],
        "tempo_map": [{"tick": t, "bpm": b / 1000.0} for t, b in dump["tempo_map"]],
        "parts": parts,
        "provenance": dump["provenance"],
    }
    provider = ManualProvider(input_fn=lambda prompt: json.dumps(session_v1),
                              output_fn=lambda *a: None)
    mockup, attempts = generate_mockup(seed, work, provider, era="baroque")
    assert attempts >= 1
    total = sum(len(v) for v in mockup["parts"].values())
    assert total == work.note_count  # full coverage, fidelity guard


def test_committed_expressive_mockup_is_non_flat():
    """The spike's recorded artifact: non-flat where the stand-in is flat."""
    stand_in = load_mockup(open(os.path.join(
        REPO, "seeds", "bwv227.1.v2.mockup.json")).read())
    expressive = load_mockup(open(EXPRESSIVE).read())
    si, ei = (extract_interpretation(stand_in),
              extract_interpretation(expressive))
    assert si.velocity_pstdev == 0.0  # stand-in is flat by construction
    assert ei.velocity_pstdev > 0     # the ManualProvider path is not
    assert ei.rubato_pstdev_ms > 0
    assert len(expressive.notes) == len(stand_in.notes)


def test_expressive_mockup_provenance():
    raw = json.load(open(EXPRESSIVE))
    assert raw["provenance"]["seed_hash"], "lineage pointer present"
    assert raw["provenance"]["operation"] == "manual-provider-spike@1"
