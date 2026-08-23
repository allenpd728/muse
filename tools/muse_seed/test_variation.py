"""S3.4 variation points tests (issue #145).

Region/kind/budget/assertions structure; constraint schema checker;
work-bounds checking against the IR duration.
"""

import pytest

from muse_seed.seed import Seed, SeedError, validate_seed
from muse_seed.variation import (
    KINDS,
    VariationError,
    VariationPoint,
    validate_variation_points,
)


def vp_dict(**kw):
    d = {"region": [0, 480], "kind": "ornament"}
    d.update(kw)
    return d


class TestSchema:
    def test_minimal_point_valid(self):
        vp = VariationPoint.from_dict(vp_dict())
        assert vp.budget == 0.2  # default
        assert vp.assertions == {}

    def test_all_kinds_accepted(self):
        for kind in sorted(KINDS):
            VariationPoint.from_dict(vp_dict(kind=kind))

    def test_unknown_kind_rejected(self):
        with pytest.raises(VariationError, match="unknown kind"):
            VariationPoint.from_dict(vp_dict(kind="vibrato"))

    def test_unknown_keys_rejected(self):
        with pytest.raises(VariationError, match="unknown keys"):
            VariationPoint.from_dict(vp_dict(vibe="loose"))

    def test_region_shape_enforced(self):
        for bad in ([0], [0, 480, 960], "0-480", [0.0, 480.0], None):
            with pytest.raises(VariationError, match="region"):
                VariationPoint.from_dict(vp_dict(region=bad))

    def test_kind_required(self):
        d = vp_dict()
        del d["kind"]
        with pytest.raises(VariationError, match="kind is required"):
            VariationPoint.from_dict(d)

    def test_empty_region_rejected(self):
        with pytest.raises(VariationError, match="non-empty"):
            VariationPoint.from_dict(vp_dict(region=[480, 480]))
        with pytest.raises(VariationError, match="non-empty"):
            VariationPoint.from_dict(vp_dict(region=[960, 480]))

    def test_negative_start_rejected(self):
        with pytest.raises(VariationError, match="negative"):
            VariationPoint.from_dict(vp_dict(region=[-10, 480]))

    @pytest.mark.parametrize("budget", [-0.1, 1.1])
    def test_budget_bounds(self, budget):
        with pytest.raises(VariationError, match="budget"):
            VariationPoint.from_dict(vp_dict(budget=budget))

    def test_attachable_assertions(self):
        VariationPoint.from_dict(vp_dict(assertions={
            "register": {"part": "soprano", "min": "C4", "max": "A5"},
            "must_contain": [[60, 62, 64]],
        }))

    def test_unattachable_assertion_rejected(self):
        with pytest.raises(VariationError, match="unattachable"):
            VariationPoint.from_dict(vp_dict(assertions={"vibe_check": True}))

    def test_round_trip(self):
        vp = VariationPoint.from_dict(vp_dict(
            region=[480, 960], kind="cadenza", budget=0.5,
            assertions={"tempo_bounds": {"min_bpm": 40}}, label="fermata cadenza"))
        assert VariationPoint.from_dict(vp.to_dict()) == vp


class TestListValidation:
    def test_overlapping_regions_rejected(self):
        with pytest.raises(VariationError, match="overlapping"):
            validate_variation_points([vp_dict(region=[0, 480]),
                                       vp_dict(region=[240, 720])])

    def test_adjacent_regions_accepted(self):
        validate_variation_points([vp_dict(region=[0, 480]),
                                   vp_dict(region=[480, 960])])

    def test_region_outside_work_rejected(self):
        with pytest.raises(VariationError, match="exceeds work duration"):
            validate_variation_points([vp_dict(region=[0, 1000])],
                                      duration_ticks=960)

    def test_region_inside_work_accepted(self):
        validate_variation_points([vp_dict(region=[0, 960])], duration_ticks=960)

    def test_non_list_rejected(self):
        with pytest.raises(VariationError, match="must be a list"):
            validate_variation_points("not-a-list")

    def test_non_mapping_entry_rejected(self):
        with pytest.raises(VariationError, match="must be a mapping"):
            validate_variation_points([42])


class TestSeedIntegration:
    def make_seed(self, variation_points):
        return Seed(format_version="0.1", work_id="byrd-mass3v",
                    params={"tempo": {"min_bpm": 60, "max_bpm": 120, "default_bpm": 96}},
                    variation_points=variation_points,
                    assertions={"must_contain": [[60, 62]]})

    def test_valid_points_pass_seed_validation(self):
        validate_seed(self.make_seed([vp_dict(), vp_dict(region=[480, 960], kind="repeat")]))

    def test_bad_point_fails_seed_validation(self):
        with pytest.raises(SeedError, match="variation_points"):
            validate_seed(self.make_seed([vp_dict(kind="vibrato")]))

    def test_empty_points_optional(self):
        validate_seed(self.make_seed([]))
