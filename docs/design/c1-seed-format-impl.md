# C1 — Seed format implementation (design doc, scaffold)

**Phase 3 — Seed authoring. Status: scaffold.**

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
