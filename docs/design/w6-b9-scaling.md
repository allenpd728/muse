# W6 — B9 compute scaling (design doc, scaffold)

**Phase 0 — Analysis workbench (sub-task). Status: scaffold.**

## Purpose

Beethoven 9 is 239,459 notes; a naive SIATEC-style pattern pass may be
infeasible. This sub-task profiles W3's analyzer on the corpus ladder,
chooses suffix-array vs. SIATEC-C vs. sampling, and pins compute budgets
per corpus tier before the Ninth's pass. Evidence source for W3's
compute-plan open question.

## Dependencies

- **Upstream:** W1 (IR), W2 (loaded corpus), W3 (analysis pattern vocab).
- **Downstream:** W3 (compute budgets pinned), all S-series (resolves the
  ladder's scale risk).

## Scope (pin in draft)

- **Inputs:** corpus ladder scales (~280, varies, 24k, 13k, 239k notes).
- **Outputs:** profiling report + scale algorithm choice + budget table.
- **Non-goals:** implementing the algorithm change (W3 owns it); this task
  is the measurement and decision.

## Open questions

- Suffix-array geometric discovery (structure-A/structure-C) vs.
  sampled/geometric SIATEC-C; tolerance for approximation under threshold.

## Acceptance criteria (when promoted to draft)

- Beethoven 9 pattern pass completes within declared budget; report
  committed; W3's compute open question resolved.
