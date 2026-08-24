# Test spec — C3 budgets calibration (task #175) — CLOSED

Written 2026-08-23 by the completing agent, per TASK_WORKFLOW §6.
Closed 2026-08-24 (run=20260824-1032-xjzf, Tests issue #215).

## Coverage landed

`tools/muse_budgets/tests/test_budgets.py` — 9 tests
(`cd tools && python -m pytest muse_budgets -q`, <1s):

- Era coverage (baroque measured, classical/romantic provisional)
- Unknown-era fallback → baroque bound + provisional flag
- suggest() schema shape (tempo min/max, dynamics bound, chord_spread)
- Chorale-measured bound pin (93-sample pstdev → 0.65)
- **Wire-in contract (gap 2, added by #215):** `_propose` returns
  `era_budget` on the seed dict — presence + exact values vs
  `suggest(era)`, schema shape, tempo default == budget midpoint,
  unknown era hint → baroque fallback + all-provisional flags,
  era_budget/provenance era_hint consistency. Author + seed_cli suites
  re-run green (23 tests).

## Residual gaps → tracked elsewhere

1. **Provisional eras measured** — blocked on C5 (Baroque-delta) and the
   delta plan's Vienna/Batik upload; re-measure and clear provisional
   when either lands. Those tasks spec their own tests.
2. **Validation-side era_budget assertion** — `muse_author` CLI drops
   `era_budget` at the Seed/YAML seam, so C1 cannot assert its presence
   on authored proposals. Needs a format decision (S3 schema field vs
   proposer-internal). Logged as
   `bugs/open_20260824-105500_author-cli-drops-era-budget.md` + issue
   #236.
3. **Corpus-size guard** — bound is pstdev<=0.65 from 93 samples (~192
   accessible; remaining chorales are duplicated ID paths). Wider
   sampling could tighten the bound; corpus expansion is the follow-up.

## Invocation

`cd tools && python -m pytest muse_budgets -q` (<1 s).
`cd tools && python -m pytest muse_author muse_seed_cli -q` (~2 s).
