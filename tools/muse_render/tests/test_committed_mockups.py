"""T6 (#275): committed-mockup render/load guard.

Every `*.mockup.json` committed under seeds/ is a loadable, renderable
artifact. Format drift must fail here loudly — the L1.11 stand-in swap
(#276) will change what these files contain, and this guard is the
contract that swap must not break.
"""

import json
import os
import sys
import wave

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from muse_mockup import load_mockup  # noqa: E402
from muse_render import render_to_file  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SEEDS = os.path.join(REPO, "seeds")


def _committed_mockups():
    return sorted(f for f in os.listdir(SEEDS) if f.endswith(".mockup.json"))


def test_at_least_one_committed_mockup():
    assert _committed_mockups(), (
        "no committed *.mockup.json under seeds/ — the guard lost its "
        "subject; either the artifacts moved or the S3.8b persistence "
        "convention changed")


@pytest.mark.parametrize("fname", _committed_mockups())
def test_mockup_loads_and_carries_valid_provenance(fname):
    path = os.path.join(SEEDS, fname)
    raw = json.load(open(path))
    m = load_mockup(open(path).read())
    assert m.notes, f"{fname}: empty note list"
    assert m.ppq > 0, f"{fname}: ppq {m.ppq}"
    assert all(n.velocity > 0 for n in m.notes), f"{fname}: dead notes"
    # L1.10 lineage pointer present and matches its sibling seed's bytes
    seed_hash = raw.get("provenance", {}).get("seed_hash")
    assert seed_hash, f"{fname}: no provenance.seed_hash"
    from muse_lineage.lineage import find_by_hash
    parent = find_by_hash(seed_hash, [SEEDS])
    assert parent, f"{fname}: seed_hash names no committed artifact"


def test_committed_chain_verifies():
    """Artifact-level pin: the v3 → mockup → v2 → root chain resolves.
    Duplicates the grow-suite pin deliberately — a format change should
    fail at the artifact level first."""
    from muse_lineage.lineage import walk
    v3 = os.path.join(SEEDS, "bwv227.1.v3.seed.yaml")
    if not os.path.exists(v3):
        pytest.skip("v3 chain not committed in this checkout")
    hops = walk(v3, [SEEDS])
    assert [h.status for h in hops] == ["verified"] * 3 + ["root"]


@pytest.mark.parametrize("fname", _committed_mockups())
def test_mockup_renders_to_nontrivial_wav(fname, tmp_path):
    m = load_mockup(open(os.path.join(SEEDS, fname)).read())
    out = tmp_path / "out.wav"
    report = render_to_file(m, str(out))
    assert report["notes"] == len(m.notes)
    assert report["duration_sec"] > 0
    assert os.path.getsize(out) > 44 * 1000  # >> WAV header
    with wave.open(str(out)) as w:
        assert w.getnframes() > 0
