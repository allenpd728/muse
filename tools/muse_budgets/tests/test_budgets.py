"""C3 budgets engine tests: era coverage, provisional marking on unknown,
the suggest() schema shape, and the C2 wire-in contract (test spec
tests/open_20260823-222856_c3-budget-calibration.md, issue #215)."""

import os

import pytest

from muse_budgets import ERA_DEFAULTS, budgets, suggest


def test_all_eras_covered():
    assert budgets("baroque").provisional is False
    assert budgets("classical").provisional is True
    assert budgets("romantic").provisional is True


def test_unknown_era_falls_back_provisional():
    b = budgets("era_that_does_not_exist")
    assert b.provisional is True
    assert b.tempo_bpm_min == ERA_DEFAULTS["baroque"].tempo_bpm_min


def test_suggest_shape():
    s = suggest("baroque")
    assert s["era"] == "baroque"
    assert s["tempo_bpm"]["min"] == 88
    assert s["tempo_bpm"]["max"] == 120
    assert s["tempo_bpm"]["provisional"] is False
    assert s["chord_spread"]["ioi_pstdev_max"] == 0.65


def test_chorale_measured_bounds():
    """93-sample chorale corpus: spreads ran 0..0.62 pstdev; bound at 0.65."""
    b = budgets("baroque")
    assert b.chord_spread_max_ioi_pstdev == 0.65


CORPUS = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                       "..", "..", "..", "corpus"))
KYRIE = os.path.join(CORPUS, "byrd", "1-Kyrie.mid")


@pytest.fixture(scope="module")
def work():
    from muse_ir import load
    return load(KYRIE)


class TestAuthorWireIn:
    """_propose must return era_budget on the seed dict (spec gap 2):
    the C3 budget is what sanctions the proposal's tempo bounds."""

    def test_era_budget_present_and_exact(self, work):
        from muse_author import propose_seed
        sd = propose_seed(work, era_hint="baroque").seed_dict
        assert sd["era_budget"] == suggest("baroque")

    def test_era_budget_schema_shape(self, work):
        from muse_author import propose_seed
        eb = propose_seed(work, era_hint="baroque").seed_dict["era_budget"]
        assert set(eb) == {"tempo_bpm", "dynamics", "chord_spread", "era"}
        assert set(eb["tempo_bpm"]) == {"min", "max", "provisional"}
        assert set(eb["dynamics"]) == {"range_max", "provisional"}
        assert set(eb["chord_spread"]) == {"ioi_pstdev_max", "provisional"}

    def test_tempo_default_is_budget_midpoint(self, work):
        from muse_author import propose_seed
        sd = propose_seed(work, era_hint="baroque").seed_dict
        t = sd["era_budget"]["tempo_bpm"]
        assert sd["params"]["tempo"]["default_bpm"] == (t["min"] + t["max"]) / 2

    def test_unknown_era_hint_proposal_marks_provisional(self, work):
        from muse_author import propose_seed
        sd = propose_seed(work, era_hint="renaissance").seed_dict
        eb = sd["era_budget"]
        assert eb["era"] == "baroque"  # conservative fallback
        assert eb["tempo_bpm"]["provisional"] is True
        assert eb["dynamics"]["provisional"] is True
        assert eb["chord_spread"]["provisional"] is True

    def test_era_budget_consistent_with_provenance_hint(self, work):
        from muse_author import propose_seed
        sd = propose_seed(work, era_hint="romantic").seed_dict
        assert sd["provenance"]["era_hint"] == "romantic"
        assert sd["era_budget"]["era"] == "romantic"
