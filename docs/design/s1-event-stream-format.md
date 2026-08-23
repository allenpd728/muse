# S1 — Event stream format (design doc)

**Phase 1 — Format spec. Status: implemented (2026-08-23, #137 →
[FORMAT_SPEC.md §4](../../FORMAT_SPEC.md) + [tools/s1_stream](../../tools/s1_stream/)).**

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

## Event log (implementation, 2026-08-23)

- **Spec pinned as FORMAT_SPEC §4** — content model = W1 IR exactly (every
  construct on the IR carries a corpus:tools/ir evidence chain; nothing
  speculative ships — locked decision "evidence-driven design").
- **ppq accepted per-source, no canonical normalization.** Measured: Bach 2,
  Byrd 192, B9 24, Schubert LCM-of-mixed-divisions. The stream records the
  source ppq in meta; re-flation stays source-exact by construction and
  avoids any LCM inflation risk.
- **Imitative entries measured at zero across the corpus (W3 report
  2026-08-23)** — pattern-factoring ships driven by exact/transposed/
  ostinato; the imitative operator is evidence-gated out of v1.0's
  construct list until a corpus work produces one.
- **Golden vectors = canonical JSON dump, verified via W4.** JSON is the
  interchange encoding only (the design doc's "binary layout" belongs to
  S2's packing — S1 pins content + contract, not bytes).
- **Dynamics curves resolved:** the score carries the marked tempo map
  only; continuous shaping is S3/L1 prompt-side, never baked into roll.
