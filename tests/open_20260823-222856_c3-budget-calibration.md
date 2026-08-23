# Test spec — C3 budgets calibration (task #175)

Written 2026-08-23 by the completing agent, per TASK_WORKFLOW §6.

## Status of coverage

C3 shipped with 4 pytest tests in tools/muse_budgets/tests/test_budgets.py,
all passing; tools/muse_author tests also pass (9 tests — including the
end-to-end CLI after pyyaml landed).

- Era coverage (baroque measured, classical/romantic provisional)
- Unknown-era fallback → baroque bound + provisional flag
- suggest() schema shape (tempo min/max, dynamics bound, chord_spread)
- Chorale-measured bound pin (93-sample pstdev → 0.65)

## Behaviors still needing coverage (gaps)

1. **Provisional eras measured.** classical/romantic stay provisional —
   C5 (Baroque-delta) and the delta plan's Vienna/Batik upload are
   the follow-up; when either lands, re-measure and clear provisional.
2. **Wire-in contract.** _propose returns era_budget on the seed;
   muse_seed_cli validation should assert its presence on authored
   proposals — test addition belongs to the C2 follow-up.
3. **Corpus-size guard.** The bound is pstdev≤0.65 from 93 samples
   (~192 accessible; the remaining chorales are duplicated ID paths).
   Wider sampling could tighten the bound; corpus-expansion is the
   follow-up.

## Invocation

`cd tools/muse_budgets && python -m pytest` (<1 s).
`cd tools/muse_author && python -m pytest` (<1 s).
