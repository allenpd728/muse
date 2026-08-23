# CI conformance gate — design doc scaffold

**Phase 2.5 — integration. Status: scaffold (awaiting issue + human sign-off).**

## Purpose

A CI job (GitHub Actions) that runs the known-answer gates: W2 corpus-loader pins, S1 golden-vector verification, S2 round-trip W4 diff, S5 container golden vectors, and the chain harness, on every push to `dev` and `main`. AGENTS.md's "CI returns with the first workflow" clause; today nothing guards a merge — the Phase 0→1→2 work has no CI floor.

## Dependencies

- **Upstream:** all landed tools with test suites (W1/W2/W3/W4/W5, S1/S2/S3/S4/S5, C1/C2); P3 (conformance-suite target when it lands).
- **Downstream:** every future merge (the gate blocks regression).

## Scope (pin in draft)

- **Inputs:** dev/main pushes, PRs.
- **Outputs:** pass/fail per gate; branch protection once stable.
- **Non-goals:** Netlify QA frontend serving (existing docs/spike publisher); release/deployment (not yet public).

## Open questions (draft-level)

- Gate split: fast (~30s, must pass) vs. slow (~5min, allow-fail initially).
- Storage: golden vectors in-repo vs. regenerated at job start (P3's open question applies).

## Acceptance criteria

- Push to dev runs the suite; a regression that changes a known-answer pin fails the job.
