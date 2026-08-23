"""Tests: S3.2 parameters + ranges (issue #157).

Spec: tests/open_20260823-211500_s3-parameters-ranges.md — budget
calibration, validation, era coverage.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_seed.params import (
    ERA_BUDGETS,
    DensityRange,
    EnergyRange,
    RangeError,
    TempoRange,
    VariationRange,
    chord_spread_ms,
    tempo_budget,
    velocity_budget,
)

ERAS = ["baroque", "classical", "romantic", "early_romantic"]


class TestBudgetCalibration:
    @pytest.mark.parametrize("era", ERAS)
    def test_tempo_budget_within_sane_bounds(self, era):
        for nominal in (60, 96, 132):
            r = tempo_budget(era, nominal)
            assert 30 <= r.min_bpm <= r.default_bpm <= r.max_bpm <= 300
            assert r.default_bpm == nominal

    def test_tempo_budget_matches_era_percentages(self):
        # classical ±35% @ 96 → [62, 129] (Vienna 4x22 evidence)
        r = tempo_budget("classical", 96)
        assert (r.min_bpm, r.max_bpm) == (62, 129)
        # baroque ±25% @ 96 → [72, 120]
        r = tempo_budget("baroque", 96)
        assert (r.min_bpm, r.max_bpm) == (72, 120)

    def test_velocity_budget_matches_delta_analysis(self):
        assert velocity_budget("romantic") == 1.45  # Magaloff spread ~145%
        assert velocity_budget("baroque") == 0.20
        assert velocity_budget("classical") == 0.18
        assert velocity_budget("early_romantic") == 0.16

    def test_chord_spread_universal(self):
        for era in ERAS:
            assert chord_spread_ms(era) in (16, 17)


class TestValidation:
    def test_tempo_default_outside_range(self):
        with pytest.raises(RangeError, match="outside"):
            TempoRange(min_bpm=60, max_bpm=120, default_bpm=200).validate()

    def test_tempo_sane_bounds(self):
        with pytest.raises(RangeError, match="sane"):
            TempoRange(min_bpm=10, max_bpm=120, default_bpm=96).validate()
        with pytest.raises(RangeError, match="sane"):
            TempoRange(min_bpm=60, max_bpm=400, default_bpm=96).validate()

    def test_energy_level_bounds(self):
        EnergyRange(level=0.0).validate()
        EnergyRange(level=1.0).validate()
        with pytest.raises(RangeError, match="energy"):
            EnergyRange(level=1.1).validate()
        with pytest.raises(RangeError, match="energy"):
            EnergyRange(level=-0.1).validate()

    def test_density_min_gt_max(self):
        with pytest.raises(RangeError, match="density"):
            DensityRange(min_notes_per_beat=4, max_notes_per_beat=2).validate()
        with pytest.raises(RangeError, match="density"):
            DensityRange(min_notes_per_beat=-1, max_notes_per_beat=2).validate()

    def test_variation_level_nonnegative(self):
        VariationRange(level=0).validate()
        with pytest.raises(RangeError, match="variation"):
            VariationRange(level=-1).validate()

    @pytest.mark.parametrize("fn", [tempo_budget, velocity_budget, chord_spread_ms])
    def test_unknown_era_rejected(self, fn):
        with pytest.raises(RangeError, match="unknown era"):
            fn("medieval", 96) if fn is tempo_budget else fn("medieval")


class TestEraCoverage:
    def test_all_four_eras_defined(self):
        assert set(ERA_BUDGETS) == set(ERAS)

    def test_budget_fields_complete(self):
        for era, budget in ERA_BUDGETS.items():
            assert set(budget) == {"tempo_pct", "velocity_pct", "chord_spread_ms"}, era
            assert 0 < budget["tempo_pct"] < 1, era
            assert budget["velocity_pct"] > 0, era
