# S1 — Event stream format (design doc, scaffold)

**Phase 1 — Format spec. Status: scaffold.**

## Purpose

The decoder↔renderer contract: binary layout, tick resolution, dynamics
curves. The on-disk freeze of W1's IR. Every player and every renderer
consumes this stream; it is versioned with the format spec.

## Dependencies

- **Upstream:** W3 (what must be representable), W4 (golden-vector
  generation).
- **Downstream:** P1 (decoder output), C1–C4 (validation targets), L1
  (mockup↔stream seam).

## Scope (pin in draft)

- **Inputs:** W1 IR content model.
- **Outputs:** spec section + golden vectors.
- **Non-goals:** language-level constructs (S4), score packing (S2).

## Open questions

- Byte layout specifics; curve encoding resolution.

## Acceptance criteria (when promoted to draft)

- Spec section written; golden vectors via W4 pass.
