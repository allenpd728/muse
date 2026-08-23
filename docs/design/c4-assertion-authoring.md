# C4 — Assertion authoring (design doc, scaffold)

**Phase 3 — Seed authoring. Status: scaffold.**

## Purpose

Human writes constraints per work: must_contain, register, form,
structural invariants. Assertions are what make boldness safe — the LLM's
mockups validate against them.

## Dependencies

- **Upstream:** C1 (seed r/w).
- **Downstream:** L1 (validation loop).

## Scope (pin in draft)

- **Inputs:** assertion vocabulary from S3/S4.
- **Outputs:** per-work assertion sets bundled in seeds.
- **Non-goals:** assertion inference from the IR (future C2 enhancement, not
  this task).

## Open questions

- Reusable assertion library vs. per-work bespoke.

## Acceptance criteria (when promoted to draft)

- Assertions validate against mockups (fail loudly on violation, pass
  silently on compliance).
