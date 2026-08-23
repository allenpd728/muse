"""C3 budgets engine tests: era coverage, provisional marking on unknown,
and the suggest() schema shape."""

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
