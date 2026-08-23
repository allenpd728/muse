# S4 — Language spec (design doc, scaffold)

**Phase 1 — Format spec. Status: scaffold.**

## Purpose

The executable layer, if needed: operators (transpose/invert/retro/aug/dim),
control flow, assertions — over the packed score. Whether the corpus demands
a general operator set or a leaner one is a W3 evidence question
(FORMAT_SPEC §8).

## Dependencies

- **Upstream:** W3 pattern report.
- **Downstream:** P1 (decoder semantics), C2-inspired authoring loops.

## Scope (pin in draft)

- **Inputs:** W3 pattern inventory by frequency.
- **Outputs:** spec section + hand-written example programs.
- **Non-goals:** generality for its own sake — a construct without corpus
  evidence doesn't ship (locked decision).

## Open questions

- Operator set: the five classics, more, or fewer.

## Acceptance criteria (when promoted to draft)

- Spec section written; hand-written example programs exercise each shipped
  construct.
