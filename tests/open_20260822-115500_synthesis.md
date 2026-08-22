# Test spec: IR → .muse.json synthesis residual coverage (follow-up to #19)

**Source task:** #19 (IR → .muse.json synthesis)
**Code under test:** `importer/synthesize.mjs` (`tests/synthesize.test.mjs` covers
the DoD: flattened globals, motif extraction + marking, default rendition,
schema validity). This spec covers what it does not.

## Behaviors to verify

- **Section detection**: a source with a genuinely repeated multi-bar block
  produces `form.sections` with `order`/`repetition` derived from recurrence,
  marked in `extensions.importer.inferred`. Current test only proves the
  negative path (no repetition → no form guess).
- **Key map flattening**: opening key becomes `globals.key`; mid-piece key
  change is dropped and marked. Needs a MusicXML fixture with a key change.
- **Atonal key**: `keyMap` entry with tonic `"atonal"` emits
  `globals.key: { tonic: "atonal" }` with no `mode` (per globals.schema).
- **Multiple parts**: motif extraction searches across parts, not within one;
  a pattern repeated *across* parts counts as a recurrence.
- **Empty IR edge**: zero parts, no tempo/meter/key — document still
  validates (tempo defaults to 120 and is marked as inferred).
- **Long-pattern preference**: a 4-note pattern nested inside a 5-note
  pattern keeps only the longer (dedup rule in `extractMotifs`).

## How to run

Extend `tests/synthesize.test.mjs`; new fixtures alongside the existing
importer fixtures. `npm test` picks the suite up automatically.
