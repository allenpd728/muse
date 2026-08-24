# L4 — Distiller (design doc)

**Phase 4 — The product. Status: implemented (2026-08-24, #196 →
[tools/muse_distill](../../tools/muse_distill/)).**

## Purpose

Mockup → extracted interpretation → seed revision. The learning loop: the
prompt accumulates interpretive craft; later mockups are cheaper and better.
Extraction borrows pyAMPACT/Parangonada/Partitura; the distillation logic is
ours.

## Dependencies

- **Upstream:** L1 (mockups to distill), C1 (seed r/w for revision output).
- **Downstream:** E1 (the event's mature seed), C2 (authoring loop feedback).

## Scope (pin in draft)

- **Inputs:** validated mockups.
- **Outputs:** seed deltas (human-reviewable).
- **Non-goals:** auto-applying revisions (human approval stays in loop).

## Open questions

- Alignment approach (per prior-art: Partitura DTW-class).

## Acceptance criteria (when promoted to draft)

- Distills a mockup into a seed delta that a human can review and apply.
