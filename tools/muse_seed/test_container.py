"""Tests: S3.1 container & encoding (issue #156).

Spec: tests/open_20260823-210000_s3-container-encoding.md — schema
validation, YAML/JSON round-trips, example seed.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_seed import Seed, SeedError, dump_seed, load_seed, validate_seed

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXAMPLE = os.path.join(REPO, "seeds", "bwv227.1.seed.yaml")


def make_seed(**kw):
    args = dict(format_version="0.1", work_id="bwv227.1",
                params={"tempo": {"min_bpm": 62, "max_bpm": 129, "default_bpm": 96}},
                assertions={"must_contain": [[71, 73, 74]]})
    args.update(kw)
    return Seed(**args)


class TestSchemaValidation:
    @pytest.mark.parametrize("missing", ["format_version", "work_id", "params", "assertions"])
    def test_missing_required_keys_rejected(self, missing):
        seed = make_seed()
        setattr(seed, missing, "" if missing in ("format_version", "work_id") else {} if missing == "assertions" else {})
        if missing == "params":
            seed.params = {}
        with pytest.raises(SeedError, match="missing required keys"):
            validate_seed(seed)

    def test_unknown_top_level_keys_rejected(self):
        seed = make_seed()
        seed.to_dict = lambda: {**Seed.to_dict(seed), "vibe": "good"}
        with pytest.raises(SeedError, match="unknown top-level keys"):
            validate_seed(seed)

    def test_params_must_be_mapping(self):
        with pytest.raises(SeedError, match="params must be a mapping"):
            validate_seed(make_seed(params=[1, 2]))

    def test_assertions_must_be_mapping(self):
        with pytest.raises(SeedError, match="assertions must be a mapping"):
            validate_seed(make_seed(assertions=["must_contain"]))

    def test_variation_points_must_be_list(self):
        with pytest.raises(SeedError, match="variation_points must be a list"):
            validate_seed(make_seed(variation_points={"region": [0, 480]}))


class TestRoundTrip:
    def test_yaml_round_trip_identical(self):
        seed = make_seed(
            philosophy={"tempo_philosophy": ["flexible"],
                        "provenance": {"author": "founder", "ai_assisted": False}},
            variation_points=[{"region": [0, 480], "kind": "ornament", "budget": 0.2,
                               "assertions": {}, "label": "opening"}],
        )
        text = dump_seed(seed, fmt="yaml")
        again = load_seed(text, fmt="yaml")
        assert again.to_dict() == seed.to_dict()

    def test_json_round_trip_identical(self):
        seed = make_seed(title="Jesu, meine Freude")
        text = dump_seed(seed, fmt="json")
        again = load_seed(text, fmt="json")
        assert again.to_dict() == seed.to_dict()

    def test_json_is_machine_fair(self):
        text = dump_seed(make_seed(), fmt="json")
        import json
        parsed = json.loads(text)  # stdlib reads it, no yaml needed
        assert parsed["work_id"] == "bwv227.1"


class TestExampleSeed:
    def test_example_loads_and_validates(self):
        seed = load_seed(open(EXAMPLE).read(), fmt="yaml")
        assert seed.work_id == "bwv227.1"
        assert seed.params["tempo"]["default_bpm"] == 96

    def test_example_round_trips_both_formats(self):
        seed = load_seed(open(EXAMPLE).read(), fmt="yaml")
        for fmt in ("yaml", "json"):
            again = load_seed(dump_seed(seed, fmt=fmt), fmt=fmt)
            assert again.to_dict() == seed.to_dict()

    def test_example_assertions_present(self):
        seed = load_seed(open(EXAMPLE).read(), fmt="yaml")
        assert "register" in seed.assertions
        assert seed.assertions["register"]["part"] == "P4"
