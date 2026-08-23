# W4 — Diff tool design doc

**Phase 0 — Analysis workbench. Status: draft (was scaffold).**

## Purpose

IR ↔ IR comparison: recall/precision in tick space, tolerance-configurable.
The ground truth for every compression claim and every conformance vector.
Automates what the spike hand-checked.

## Dependencies

- **Upstream:** W1 (IR).
- **Downstream:** S2 (round-trip validation), P3 (golden vectors), C2
  (authoring loop), L1 (mockup validation vs. assertions).

## Interface (draft)

```
muse-diff <a> <b> [--tolerance-ticks N]
  → report { recall, precision, mismatches[] }
```

Tick-space matching with deterministic pairing (sorted-onset walks).
Tolerance is a beat-relative tick window; absolute-tick mode remains a
flag, not a default. Mismatches classify (missing/extra/onset-drift/
velocity-drift) so reports are actionable rather than scalar.

## Scope

- **Inputs:** two IR streams.
- **Outputs:** numeric recall/precision + classified mismatch report.
- **Non-goals:** semantic/musicological similarity — tick-space only;
  visualization (W5).

## Open questions (draft-level)

- Pairing rule under tolerance: draft picks greedy-sorted pairing; stable
  marriage matching remains a fallback if greedy proves noisy on dense
  orchestral works.

## Acceptance criteria (when promoted to draft)

- Self-diff = 1.0; mutation tests behave (deletions degrade recall,
  insertions degrade precision, drift degrades matched quality);
  test specs open per TASK_WORKFLOW.
