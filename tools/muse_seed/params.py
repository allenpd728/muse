"""S3.2 parameters + ranges — calibrated bounds per delta-analysis.

Parameter ranges (tempo/energy/density/variation) with era-calibrated
budgets from Vienna 4x22, Magaloff, Batik, and the delta-analysis docs.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class RangeError(ValueError):
    """Raised when a parameter range violates S3.2 constraints."""


@dataclass(frozen=True)
class TempoRange:
    min_bpm: int
    max_bpm: int
    default_bpm: int

    def validate(self):
        if not (self.min_bpm <= self.default_bpm <= self.max_bpm):
            raise RangeError(f"default {self.default_bpm} outside [{self.min_bpm}, {self.max_bpm}]")
        if self.min_bpm < 30 or self.max_bpm > 300:
            raise RangeError("tempo bounds outside sane [30, 300] bpm")


@dataclass(frozen=True)
class EnergyRange:
    level: float                    # 0..1
    shape: str = "arch"             # curve_ref placeholder

    def validate(self):
        if not (0.0 <= self.level <= 1.0):
            raise RangeError(f"energy level {self.level} outside [0, 1]")


@dataclass(frozen=True)
class DensityRange:
    min_notes_per_beat: float
    max_notes_per_beat: float

    def validate(self):
        if self.min_notes_per_beat < 0 or self.max_notes_per_beat < self.min_notes_per_beat:
            raise RangeError("density bounds invalid")


@dataclass(frozen=True)
class VariationRange:
    level: int                      # 0..N
    points: list = field(default_factory=list)

    def validate(self):
        if self.level < 0:
            raise RangeError("variation level negative")


# Era-calibrated budgets from delta-analysis (docs/delta-analysis-plan.md):
# Vienna 4x22: total-duration spread ~75% → tempo ±35%
# Magaloff: velocity spread ~145–195% (Romantic)
# Chord spread ~16–17ms universal
ERA_BUDGETS = {
    "baroque": {"tempo_pct": 0.25, "velocity_pct": 0.20, "chord_spread_ms": 16},
    "classical": {"tempo_pct": 0.35, "velocity_pct": 0.18, "chord_spread_ms": 17},
    "romantic": {"tempo_pct": 0.15, "velocity_pct": 1.45, "chord_spread_ms": 16},
    "early_romantic": {"tempo_pct": 0.30, "velocity_pct": 0.16, "chord_spread_ms": 16},
}


def tempo_budget(era: str, nominal_bpm: int) -> TempoRange:
    """Compute a TempoRange from era budget + nominal tempo."""
    if era not in ERA_BUDGETS:
        raise RangeError(f"unknown era: {era}")
    pct = ERA_BUDGETS[era]["tempo_pct"]
    lo = int(nominal_bpm * (1 - pct))
    hi = int(nominal_bpm * (1 + pct))
    return TempoRange(min_bpm=lo, max_bpm=hi, default_bpm=nominal_bpm)


def velocity_budget(era: str) -> float:
    """Velocity spread percentage for an era."""
    if era not in ERA_BUDGETS:
        raise RangeError(f"unknown era: {era}")
    return ERA_BUDGETS[era]["velocity_pct"]


def chord_spread_ms(era: str) -> int:
    """Universal chord spread (melody-lead) in ms."""
    if era not in ERA_BUDGETS:
        raise RangeError(f"unknown era: {era}")
    return ERA_BUDGETS[era]["chord_spread_ms"]
