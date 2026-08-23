# Test spec — C1 seed validator

**Task:** #148 (C1 — Seed format implementation)
**Written:** 2026-08-23

## What to verify

1. **Commands**
   - `read <seed>`: prints work_id, params, philosophy, variation_points, assertions
   - `validate <seed> <work>`: schema OK → assertions OK → budget OK → exit 0
   - `budget-check <era>`: prints tempo/velocity/chord-spread for the era

2. **Failure paths**
   - Malformed seed (missing required keys) → exit 1
   - Violated assertions → exit 1
   - Unknown era in budget-check → exit 1

3. **Era-budget check**
   - provenance.era set → tempo range checked against era budget
   - provenance.era missing → skipped (back-compatible)

## How to run

```bash
python3 tools/muse_seed_cli/cli.py validate seeds/bwv227.1.seed.yaml corpus/bach/bwv227.1.mxl
```
