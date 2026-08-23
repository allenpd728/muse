"""muse_seed_cli — C1: seed validator micro-pipeline.

Read/write seeds, validate budgets against era-calibrated ranges, check
assertions against corpus works. The tester/validator session's first
claimable workbench.
"""

from .cli import main

__all__ = ["main"]
