"""L1.4 integration test (issue #209): one corpus work through the real
generate loop with a recorded LLM fixture, then the growth harness
consumes the real mockup path (stand_in: false).
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_ir import load  # noqa: E402
from muse_provider import RecordedProvider  # noqa: E402
from muse_seed import load_seed  # noqa: E402

from muse_generate.generate import assemble_prompt, generate_mockup  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WORK = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")
SEED = os.path.join(REPO, "seeds", "bwv227.1.seed.yaml")
FIXTURE = os.path.join(REPO, "tests", "fixtures", "bwv227.1.recorded-mockup.json")


@pytest.fixture(scope="module")
def seed_work():
    return load_seed(open(SEED).read(), fmt="yaml"), load(WORK)


def test_fixture_exists_and_is_schema_valid():
    mockup = json.load(open(FIXTURE))
    from muse_mockup.schema import validate_mockup_schema

    assert validate_mockup_schema(mockup)
    assert mockup["work_id"] == "bwv227.1"
    assert len(mockup["parts"]) == 4


def test_loop_end_to_end_with_recorded_fixture(seed_work):
    seed, work = seed_work
    mockup = json.load(open(FIXTURE))
    provider = RecordedProvider({str(hash(assemble_prompt(seed, work))): mockup})
    result, attempts = generate_mockup(seed, work, provider)
    assert attempts == 1
    assert result["work_id"] == "bwv227.1"
    assert all(p in result["parts"] for p in ("P1", "P2", "P3", "P4"))


def test_mockup_covers_all_score_notes(seed_work):
    """Every score note index appears in the mockup (fidelity coverage)."""
    _, work = seed_work
    mockup = json.load(open(FIXTURE))
    for part in work.parts:
        indices = {n["i"] for n in mockup["parts"][part.id]}
        assert indices == set(range(len(part.notes))), (
            f"{part.id}: mockup covers {len(indices)}/{len(part.notes)} notes"
        )


def test_growth_harness_consumes_real_mockup(seed_work):
    """The distiller's seed_revision works on the real mockup — the
    growth harness's real path (stand_in: false) when it swaps."""
    from muse_distill import seed_revision

    mockup_data = json.load(open(FIXTURE))
    from muse_mockup import Mockup, Note

    mockup = Mockup(work_id=mockup_data["work_id"])
    for part_id, notes in mockup_data["parts"].items():
        for n in notes:
            mockup.notes.append(Note(
                pitch=60, onset=n["i"], duration=1, velocity=n["velocity"],
                part=part_id,
            ))
    delta = seed_revision(mockup)
    assert delta["work_id"] == "bwv227.1"
    assert delta["provenance"]["note_count"] > 0
    # the real mockup's velocity varies → pstdev > 0 (growth signal)
    assert delta["params"]["dynamics"]["velocity_pstdev"] > 0
