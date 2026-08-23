# C2 — AI-assisted authoring (design doc, scaffold)

**Phase 3 — Seed authoring. Status: scaffold.**

## Purpose

LLM analyzes the IR → proposes a seed (budgets, philosophy, variation
points). A human reviews, edits, approves. The workbench loop; spike lessons
(the mockup is dense DNA, not sketches) apply here as authoring targets.

## Dependencies

- **Upstream:** C1 (seed r/w), W1 (IR access), W4 (validation where
  assertion-like checks are generated).
- **Downstream:** feeds approved seeds into L1.
- **Critical path:** C1 → **C2** → L1 → L2.

## Scope (pin in draft)

- **Inputs:** IR of a corpus work, seed library.
- **Outputs:** human-approved seed for one corpus work.
- **Non-goals:** autonomous seed generation (human review is mandatory per
  FORMAT_SPEC §5).

## Open questions

- Which LLM + prompt design (prior-art: structured output + validate loop).

## Acceptance criteria (when promoted to draft)

- Authors a valid seed for one corpus work, human-approved.
