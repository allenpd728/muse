"""Tests: S3.4 follow-up (issue #150) — assertion evaluation end-to-end.

Gap 1 from the spec: a variation point's attached assertion, evaluated
against a real corpus work (the performance), fails loudly naming the
violation. Gaps 2–3 (kind semantics, budget calibration) belong to L1/C3
and are out of scope here.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_assert import AssertionError, validate_assertions  # noqa: E402
from muse_ir import load  # noqa: E402
from muse_seed.variation import VariationPoint  # noqa: E402

CORPUS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "corpus"))
BACH1 = os.path.join(CORPUS, "bach", "bwv227.1.mxl")


@pytest.fixture(scope="module")
def bach():
    return load(BACH1)


def make_region_assertion_vp(assertions):
    return VariationPoint.from_dict({
        "region": [0, 152], "kind": "ornament", "budget": 0.2,
        "assertions": assertions, "label": "opening phrase",
    })


class TestAttachedAssertionEndToEnd:
    def test_satisfied_assertion_passes(self, bach):
        vp = make_region_assertion_vp(
            {"register": {"part": "P4", "min": "C2", "max": "C4"}})
        validate_assertions(bach, vp.assertions)  # must not raise

    def test_violated_assertion_fails_loudly_naming_part(self, bach):
        vp = make_region_assertion_vp(
            {"register": {"part": "P4", "min": "C2", "max": "A3"}})
        with pytest.raises(AssertionError, match=r"\[register\]"):
            validate_assertions(bach, vp.assertions)

    def test_error_names_the_violating_pitch(self, bach):
        vp = make_region_assertion_vp(
            {"register": {"part": "P4", "min": "C2", "max": "A3"}})
        try:
            validate_assertions(bach, vp.assertions)
            pytest.fail("expected AssertionError")
        except AssertionError as e:
            assert "P4" in str(e)
            assert "59" in str(e)  # B3 — the out-of-register note

    def test_region_carries_assertion_through_schema(self):
        vp = make_region_assertion_vp(
            {"register": {"part": "P4", "min": "C2", "max": "C4"}})
        assert vp.assertions["register"]["part"] == "P4"
        assert vp.label == "opening phrase"

    def test_must_contain_on_real_work(self, bach):
        # Bach mvt 1 soprano opens B4 C#5 D5 = 71, 73, 74
        vp = make_region_assertion_vp({"must_contain": [[71, 73, 74]]})
        validate_assertions(bach, vp.assertions)

    def test_must_contain_failure_names_theme(self, bach):
        vp = make_region_assertion_vp({"must_contain": [[71, 72, 74]]})
        with pytest.raises(AssertionError, match="must_contain"):
            validate_assertions(bach, vp.assertions)
