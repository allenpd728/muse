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

## Closed 2026-08-24 (#220, run=20260824-1107-409b)

Landed in tools/muse_compare/tests/test_compare_gaps.py (7 tests):

- **Gap 3 (A/B delta stats):** a per-pair tempo delta over the seed
  artifacts the rig writes — computable from artifacts alone,
  antisymmetric, and sensitive to the rig's default_bpm perturbation
  (min/max stay shared; only default moves). Mockup-level IOI/dynamics
  deltas still wait on real mockups (gap 1).
- **Gap 1 seam pins:** artifacts carry per-model provenance labels, and
  the model label + tempo bump are the *only* differences between seeds —
  anything else drifting would break blinding.
- **Gap 4 (persistence within the rig's guarantee):** re-running the same
  roster reproduces byte-identical artifacts and ledger, so per-work
  archival is "keep the dir". Cross-session roster persistence remains a
  follow-up feature, not testable against today's per-run design.

Not covered, per the spec's own deferral: real LLM endpoint calls (gap 1)
and the blind listening page (gap 2, explorer QA path).
