"""Generate/validate/fix loop tests (issue #208). Recorded providers only."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_ir import load  # noqa: E402
from muse_provider import RecordedProvider  # noqa: E402
from muse_seed import load_seed  # noqa: E402

from muse_generate.generate import (  # noqa: E402
    GenerateError,
    assemble_prompt,
    generate_mockup,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WORK = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")
SEED = os.path.join(REPO, "seeds", "bwv227.1.seed.yaml")


@pytest.fixture(scope="module")
def seed_work():
    return load_seed(open(SEED).read(), fmt="yaml"), load(WORK)


def _valid_mockup(work):
    return {
        "work_id": "bwv227.1",
        "tempo_map": [{"tick": 0, "bpm": 96.0}],
        "parts": {
            p.id: [{"i": j, "velocity": 64} for j, n in enumerate(p.notes[:2])]
            for p in work.parts
        },
        "seed": {"note": "recorded"},
    }


def test_assemble_prompt_includes_seed_and_work(seed_work):
    seed, work = seed_work
    prompt = assemble_prompt(seed, work)
    assert "bwv227.1" in prompt
    assert "P1" in prompt
    assert "tempo" in prompt.lower()
    assert "philosophy" in prompt.lower()


def test_prompt_includes_prior_violation_on_retry(seed_work):
    seed, work = seed_work
    prompt = assemble_prompt(seed, work, prior_violation=["schema: tempo_map unordered"])
    assert "Prior violation" in prompt
    assert "unordered" in prompt


def test_generate_passes_on_valid_mockup(seed_work):
    seed, work = seed_work
    mockup = _valid_mockup(work)
    provider = RecordedProvider({str(hash(assemble_prompt(seed, work))): mockup})
    result, attempts = generate_mockup(seed, work, provider)
    assert result == mockup
    assert attempts == 1


def test_generate_retries_on_violation_then_passes(seed_work):
    seed, work = seed_work
    bad = {"work_id": "x", "tempo_map": [{"tick": 5, "bpm": 0}], "parts": {}}
    good = _valid_mockup(work)
    provider = RecordedProvider({
        str(hash(assemble_prompt(seed, work))): bad,
        str(hash(assemble_prompt(seed, work, prior_violation=["schema: tempo_map.5: bpm out of range"]))): good,
    })
    result, attempts = generate_mockup(seed, work, provider)
    assert result == good
    assert attempts == 2


def test_generate_fails_loudly_after_max_attempts(seed_work):
    seed, work = seed_work
    bad = {"work_id": "x", "tempo_map": [{"tick": 5, "bpm": 0}], "parts": {}}
    # every retry prompt maps to the same bad mockup → exhaustion
    provider = RecordedProvider({
        str(hash(assemble_prompt(seed, work))): bad,
        str(hash(assemble_prompt(seed, work, prior_violation=["schema: tempo_map.5: bpm out of range"]))): bad,
        str(hash(assemble_prompt(seed, work, prior_violation=["schema: tempo_map.5: bpm out of range", "schema: tempo_map.5: bpm out of range"]))): bad,
    })
    with pytest.raises(GenerateError, match="after 3 attempts") as exc:
        generate_mockup(seed, work, provider, max_attempts=3)
    assert exc.value.violations


def test_generate_wraps_provider_failure(seed_work):
    seed, work = seed_work
    provider = RecordedProvider({})  # no recording → ProviderError
    with pytest.raises(GenerateError, match="provider failed"):
        generate_mockup(seed, work, provider)
