# L1 — Mockup harness (design doc, scaffold)

**Phase 4 — The product. Status: scaffold.**

## Purpose

score + seed → LLM → mockup at full DNA density (tempo map, curves,
velocities, balance, per-note devices incl. chord spread). Generate →
validate → fix, bounded retries, fail loudly. Provenance stamped by the
harness, never trusted to the model.

## Dependencies

- **Upstream:** C1–C4 (seeds to consume), S1 (event stream seam), P2
  (renderer base for smoke), W4 (validation where applicable).
- **Downstream:** L2 (renders mockups), L3 (comparisons), L4 (distillation).

## Scope (pin in draft)

- **Inputs:** `.mu` score + seed (+ mockup schema, defined here).
- **Outputs:** mockup session files + validation reports.
- **Non-goals:** rendering (L2), model training (locked: none).

## Open questions

- Mockup schema field set (delta-analysis-derived; chord spread first-class);
  retry policy and validation order.

## Acceptance criteria (when promoted to draft)

- Produces a complete mockup for one corpus work, validated against its
  seed's assertions.
