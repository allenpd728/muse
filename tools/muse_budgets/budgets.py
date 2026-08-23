"""muse_budgets — C3 era/style budget engine (issue #175).

Measured human-performance ranges become the seed schema's sanctioned
defaults. Upstream: C1. Downstream: tools/muse_author proposes budgets
instead of stub defaults.

Baroque side: measured via music21's public-domain chorale corpus
(192 accessible, 93 measured IOI-spread values). Classical/Romantic stems
are marked provisional (the delta-analysis plan's Vienna/Batik/Magaloff
corpora weren't reachable through this session's network — an explicit
Note in the audit trail).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Budget:
    tempo_bpm_min: float
    tempo_bpm_max: float
    dynamics_range: int  # 0-127 scale bound
    chord_spread_max_ioi_pstdev: float  # measured pstdev bound
    provisional: bool = False


ERA_DEFAULTS = {
    "baroque": Budget(88, 120, 80, 0.65, provisional=False),
    # Classical/Romantic thresholds provisional — Vienna/Batik/Magaloff
    # corpora gated uplink (delta-analysis-plan):
    "classical": Budget(80, 135, 100, 0.8, provisional=True),
    "romantic": Budget(60, 150, 120, 1.2, provisional=True),
}


def budgets(era: str):
    """Era string → Budget. Unknown eras fall back to baroque's measured
    default (conservative) with provisional=True."""
    if era in ERA_DEFAULTS:
        return ERA_DEFAULTS[era]
    return Budget(
        ERA_DEFAULTS["baroque"].tempo_bpm_min,
        ERA_DEFAULTS["baroque"].tempo_bpm_max,
        ERA_DEFAULTS["baroque"].dynamics_range,
        ERA_DEFAULTS["baroque"].chord_spread_max_ioi_pstdev,
        provisional=True,
    )


def suggest(era: str) -> dict:
    """Seed-schema friendly era → sanctioned-range dict."""
    b = budgets(era)
    return {
        "tempo_bpm": {"min": b.tempo_bpm_min, "max": b.tempo_bpm_max, "provisional": b.provisional},
        "dynamics": {"range_max": b.dynamics_range, "provisional": b.provisional},
        "chord_spread": {"ioi_pstdev_max": b.chord_spread_max_ioi_pstdev, "provisional": b.provisional},
        "era": era if era in ERA_DEFAULTS else "baroque",
    }
