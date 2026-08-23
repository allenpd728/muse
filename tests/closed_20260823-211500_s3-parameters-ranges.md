# Test spec — S3.2 parameters + ranges — CLOSED

**Task:** #143 (S3.2 — Parameters + ranges)
**Written:** 2026-08-23

**Resolution (Tests: #157, 2026-08-23):** landed as
`tools/muse_seed/test_params.py` — 17 tests covering all three spec
sections: budget calibration (tempo budgets match era percentages with the
Vienna 4x22 classical pin [62, 129] @ 96; velocity matches Magaloff
percentages; chord spread universal 16–17ms), validation (all four range
types reject out-of-bounds loudly, unknown era rejected), era coverage
(all four eras, complete budget fields). Package: 115 passed, 1 skipped.

## What to verify

1. **Budget calibration**
   - tempo_budget(era, nominal) → TempoRange within [30, 300] bpm
   - velocity_budget(era) matches delta-analysis percentages
   - chord_spread_ms(era) = 16–17ms universal

2. **Validation**
   - TempoRange: default outside [min, max] → RangeError
   - EnergyRange: level outside [0, 1] → RangeError
   - DensityRange: min > max → RangeError
   - Unknown era → RangeError

3. **Era coverage**
   - baroque, classical, romantic, early_romantic all defined

## How to run

```bash
python3 -c "from muse_seed.params import tempo_budget, velocity_budget, chord_spread_ms; ..."
```
