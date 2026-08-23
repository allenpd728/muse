"""Tests: S3.6 example seed (issue #159).

Spec: tests/open_20260823-214500_s3-example-seed.md — seed validity,
self-validation against its source work, round-trips.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))

from muse_assert import validate_assertions  # noqa: E402
from muse_ir import load  # noqa: E402
from muse_seed import dump_seed, load_seed, validate_seed  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXAMPLE = os.path.join(REPO, "seeds", "bwv227.1.seed.yaml")
SOURCE = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")


@pytest.fixture(scope="module")
def seed():
    return load_seed(open(EXAMPLE).read(), fmt="yaml")


@pytest.fixture(scope="module")
def work():
    return load(SOURCE)


class TestSeedValidity:
    def test_loads(self, seed):
        assert seed.work_id == "bwv227.1"
        assert seed.title

    def test_validate_seed_passes(self, seed):
        validate_seed(seed)  # required keys, types, philosophy, variation points

    def test_provenance_discloses_ai(self, seed):
        assert seed.provenance["ai_assisted"] is True
        assert seed.provenance["source"] == "corpus/bach/bwv227.1.mxl"

    def test_philosophy_block_valid(self, seed):
        assert seed.philosophy["tempo_philosophy"] == ["flexible", "architectural"]
        assert seed.philosophy["provenance"]["ai_assisted"] is True


class TestSelfValidation:
    def test_own_assertions_pass_against_source(self, seed, work):
        validate_assertions(work, seed.assertions)

    def test_register_pin(self, seed, work):
        # P4 (bass) spans F2..C4; the seed's C2..C4 must hold
        p4 = next(p for p in work.parts if p.id == "P4")
        pitches = [n.pitch for n in p4.notes if n.pitch is not None]
        assert min(pitches) >= 36  # C2
        assert max(pitches) <= 60  # C4

    def test_tempo_bounds_pin(self, seed, work):
        lo = seed.assertions["tempo_bounds"]["min_bpm"]
        hi = seed.assertions["tempo_bounds"]["max_bpm"]
        for _tick, mbpm in work.maps.tempo:
            assert lo <= mbpm / 1000 <= hi

    def test_params_tempo_covers_source_marking(self, seed, work):
        # the work's notated 96 bpm sits inside the seed's sanctioned range
        t = seed.params["tempo"]
        assert t["min_bpm"] <= 96 <= t["max_bpm"]
        assert work.maps.tempo[0][1] == 96000


class TestRoundTrip:
    @pytest.mark.parametrize("fmt", ["yaml", "json"])
    def test_dump_load_identical(self, seed, fmt):
        again = load_seed(dump_seed(seed, fmt=fmt), fmt=fmt)
        assert again.to_dict() == seed.to_dict()
