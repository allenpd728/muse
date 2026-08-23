# S2 — Score encoding (design doc, scaffold)

**Phase 1 — Format spec. Status: scaffold.**

## Purpose

How the fixed score is packed: columnar, delta-encoded onsets, dictionary-
coded repeated patterns, entropy-coded residual. Pattern-factoring driven by
W3 evidence. Lossless against source, proven by W4.

## Dependencies

- **Upstream:** W3 (pattern statistics), W4 (round-trip proof).
- **Downstream:** P1 (decoder input).

## Scope (pin in draft)

- **Inputs:** IR (W1), W3 pattern inventory.
- **Outputs:** spec section + lossless codec behavior on the corpus.
- **Non-goals:** the seed (S3), the container (S5).

## Open questions

- Columnar layout order; entropy coder choice (off-the-shelf vs. custom).

## Acceptance criteria (when promoted to draft)

- Round-trips the corpus losslessly per W4.
