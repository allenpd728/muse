# Test spec — S3.2 parameters + ranges

**Task:** #143 (S3.2 — Parameters + ranges)
**Written:** 2026-08-23

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
