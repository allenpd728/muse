# Test spec — C2 AI-assisted authoring — CLOSED

**Task:** #153 (C2 — AI-assisted authoring)
**Written:** 2026-08-23

**Resolution (Tests: #160, 2026-08-23):** landed as
`tools/muse_author/test_author.py` — 9 tests covering all three spec
sections: proposal (required schema keys, determinism, S3.3 philosophy
format with lists + provenance, schema validation of the proposal itself,
classical default era, register derived from the work), end-to-end loop
(Bach and Byrd proposals validate exit 0 through the C1 validator),
failure paths (missing work fails loudly).

## What to verify

1. **Proposal**
   - propose_seed(work, era) returns seed dict with required schema keys
   - Deterministic (same input → same proposal)
   - Philosophy format matches sibling S3.3 spec (lists + provenance with author/ai_assisted)

2. **End-to-end loop**
   - CLI <work> → validates via muse_seed_cli._validate → exit 0
   - Assertions check against source work
   - Budgets within era-calibrated ranges

3. **Failure paths**
   - Invalid proposed seed → exit 1 with C1 validator report
   - Missing era hint → default classical

## How to run

```bash
python3 tools/muse_author/cli.py corpus/bach/bwv227.1.mxl --era classical
```
