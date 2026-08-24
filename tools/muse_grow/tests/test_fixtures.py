"""G3 iteration fixtures (issue #205): two committed seed revisions and
their expected growth report. Known-answer tests for the harness's compare.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from muse_grow.grow import compare_deltas  # noqa: E402

FIXTURES = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "tests", "fixtures")
)


def test_fixtures_exist():
    for name in ("bwv227.1.delta.v1.json", "bwv227.1.delta.v2.json",
                 "bwv227.1.growth.v1-to-v2.json"):
        assert os.path.exists(os.path.join(FIXTURES, name)), name


def test_v1_to_v2_growth_matches_expected():
    v1 = json.load(open(os.path.join(FIXTURES, "bwv227.1.delta.v1.json")))
    v2 = json.load(open(os.path.join(FIXTURES, "bwv227.1.delta.v2.json")))
    expected = json.load(open(os.path.join(FIXTURES, "bwv227.1.growth.v1-to-v2.json")))
    report = compare_deltas(v2, v1, "bwv227.1")
    for trait, want in expected.items():
        got = report.traits[trait]
        assert got["verdict"] == want["verdict"], (
            f"{trait}: expected {want['verdict']}, got {got['verdict']}"
        )


def test_seed_revisions_differ():
    import re

    v1 = open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "seeds", "bwv227.1.v1.seed.yaml")).read()
    v2 = open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "seeds", "bwv227.1.v2.seed.yaml")).read()
    assert v1 != v2
    # v2 is the growth-target: tighter tempo bounds, higher energy
    assert "min_bpm: 80" in v2
    assert "level: 0.75" in v2
