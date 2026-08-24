"""muse_grow — G1 seed growth harness (issue #203).

Close the iteration loop: seed → mockup (L1) → distill (L4) → revised-seed
delta → compare against the prior iteration's delta → growth report. The
workbench answers 'is the seed holding landmarks' (regression); this
answers 'is the seed growing' (trajectory).
"""

from .grow import GrowthReport, compare_deltas, grow_one

__all__ = ["GrowthReport", "compare_deltas", "grow_one"]
