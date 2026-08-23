# S6 — Vocal text schema (design doc, scaffold)

**Phase 1 — Format spec (sub-task). Status: scaffold.**

## Purpose

FORMAT_SPEC §8 flags vocal/choral text as a Phase 0/1 pin: the Ninth's 52
staves include chorus/soloists, and S1 needs to carry interleaved lyrics /
syllables with tick positions. This sub-task drafts the lyric schema,
validated against Beethoven 9's finale.

## Dependencies

- **Upstream:** S1 (stream mechanics); W1 (notation-umbrella detail).
- **Downstream:** S1 closure; v1.0 target passage.

## Scope (pin in draft)

- **Inputs:** S1 draft; Beethoven 9 source.
- **Outputs:** lyric schema section + golden example.
- **Non-goals:** phonetic/singing synthesis (renderer territory).

## Open questions

- Interleaved vs. sidecar lyric encoding; syllable segmentation from
  source.

## Acceptance criteria (when promoted to draft)

- Schema section committed; Beethoven 9 finale lyric example validates.
