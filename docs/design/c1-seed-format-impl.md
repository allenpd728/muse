# C1 — Seed format implementation (design doc, scaffold)

**Phase 3 — Seed authoring. Status: implemented (dev, issue #148).**

## Purpose

S3's spec → working reader/writer + validator. The tool every seed task and
the L-series harness uses to handle seeds. Reads/writes valid seeds and
validates against S3.

## Dependencies

- **Upstream:** S3 (the frozen format).
- **Downstream:** C2, C3, C4 (authoring), L1 (consumption).
- **Critical path:** W1 → W3 → S3 → **C1** → C2 → L1 → L2.

## Scope (pin in draft)

- **Inputs:** S3 spec.
- **Outputs:** seed library (read/write/validate).
- **Non-goals:** authoring intelligence (C2), budget heuristics (C3).

## Open questions

- Language/runtime choice for the workbench (aligns with W-series tools).

## Acceptance criteria (when promoted to draft)

- Reads/writes valid seeds; validator catches malformed seeds.

## Event log (implementation, 2026-08-23)

- Landed as `tools/muse_seed/cli.py` on the S3.1 library surface:
  `validate <seed.yaml> [--work <corpus-file>]` chains schema (S3.1) → era
  budgets (S3.2) → philosophy (S3.3) → variation points (S3.4) →
  assertions against the loaded work (S3.5, via muse_assert); exit 0/1.
  Work resolution defaults to the seed's `provenance.source`.
- Budget check implemented for tempo (range must fit some era's calibrated
  budget around its own default); energy/density/variation checks deferred
  to the Tests: follow-up — their consumer story belongs to C3.
- The S3.6 example seed was updated to the current schema (S3.3 philosophy
  lists + provenance landed after it): philosophy values are lists,
  `provenance.ai_assisted: true` disclosed.
- Runtime: Python, aligned with the W-series tools (open question closed).
