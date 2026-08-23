# W4 — Diff tool (design doc, scaffold)

**Phase 0 — Analysis workbench. Status: scaffold.**

## Purpose

IR ↔ IR comparison: recall/precision in tick space, tolerance-configurable.
The ground truth for every compression claim and every conformance vector.
Automates what the spike hand-checked.

## Dependencies

- **Upstream:** W1.
- **Downstream:** S2 (round-trip validation), P3 (golden vectors), C2
  (authoring loop), L1 (mockup validation vs. assertions).

## Scope (pin in draft)

- **Inputs:** two IR streams.
- **Outputs:** numeric recall/precision metric + mismatch report.
- **Non-goals:** semantic/musicological similarity — tick-space only.

## Open questions

- Tolerance model (absolute ticks vs. beat-relative).

## Acceptance criteria (when promoted to draft)

- Self-diff = 1.0; mutation tests behave (deletions degrade recall,
  insertions degrade precision).
