# Test spec — C1 seed validator — CLOSED

**Task:** #148 (C1 — Seed format implementation)
**Written:** 2026-08-23

**Resolution (Tests: #161, 2026-08-23):** landed as
`tools/muse_seed_cli/test_seed_cli.py` — 14 tests covering all three spec
sections: commands (read prints summary; validate chains schema →
assertions → budgets exit 0; budget-check prints era budgets for all four
eras), failure paths (malformed seed, violated assertions, unknown era
rejected by argparse), era-budget check (provenance.era checked against
era budget with the within/outside message pinned; missing era skipped).

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
