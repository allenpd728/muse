# Test spec — L3 model comparison rig (task #195)

Written 2026-08-24 by the completing session, per TASK_WORKFLOW §6.

## Status of coverage

5 pytest tests in tools/muse_compare/tests/test_compare.py, all passing:
- Seed variants are deterministic per model label
- Distinct models produce distinct hashes (rig distinguishes conductors)
- Artifacts written per model + ledger.json
- Ledger hashes match file contents
- Single-model edge case

Run: `cd tools/muse_compare && python -m pytest` (<1 s).

## Behaviors still needing coverage (gaps)

1. **Real LLM harness integration.** This rig plugs the mockup seam with
   deterministic per-model seed variants; actual API calls to real model
   endpoints belong to the conductor's own infra and are a live integration
   task (not this rig's tests).
2. **Blind listening page.** The ledger.json's hash-only mapping is the
   blinding interface; a listening page/UI that hides the mapping until
   verdict is recorded (spike's listener graduated) is a separate issue
   (the explorer QA path is running).
3. **A/B diff stats across models.** The DoD mentions derived delta stats
   (IOI, dynamics curves) per model pair — that layer is a follow-up so
   the ledger and its delta live together.
4. **Model registry persistence.** Roster/ledger should persist per work
   across sessions; currently per-run.

## Invocation

`cd tools/muse_compare && python -m pytest` (<1 s).
