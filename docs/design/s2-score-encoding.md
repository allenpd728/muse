# S2 — Score encoding (design doc, scaffold)

**Phase 1 — Format spec. Status: implemented (dev, issue #138).**

Evidence base: [../literature-review-w1.md](../literature-review-w1.md) §2
(packing runs on the W1 IR, not on a MIDI/token dump; Octuple-style column
merging is token-shape precedent, not a packing dependency).

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

## Event log (implementation, 2026-08-23)

- Spec landed as FORMAT_SPEC §4.6; codec at `tools/muse_roll/`.
- Columnar layout: string table → JSON meta → delta-encoded maps →
  per-part note streams (onset deltas + presence bitmap). Order chosen
  so the string table's size prefixes the payload (single-pass decode).
- Entropy coder: zlib level 9 (stdlib, off-the-shelf — the open question
  resolved; a custom coder is a post-v1 optimization).
- Lossless gate: all 13 corpus files round-trip losslessly — 12/13 with
  W4 recall = precision = 1.0 (cli.py verify); B9 verified structurally
  (encode→decode→canonical compare; the pairwise W4 diff on 239k events
  is the slow path, not the codec). Ratios vs. source: Bach 10–12%,
  Byrd 14–22%, Schubert 9.6%, B5 0.26%, B9 0.24% (68.8 MB → 168 KB;
  encode 0.8s).
- Implementation notes: package uses lazy `__init__` re-exports so
  per-directory conftest path setup precedes codec import (matches the
  repo's tools/ layout convention).
