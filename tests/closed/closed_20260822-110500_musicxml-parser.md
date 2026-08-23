# Test spec — Batch 2 #18: MusicXML parser → IR

**Source task:** #18 (MusicXML parser → IR)
**Code under test:** `importer/musicxml.mjs`; fixture `importer/fixtures/bwv269.mxl`
(public-domain Bach chorale from the music21 corpus).

Baseline coverage landed with the task: `tests/musicxml.test.mjs` — 14 checks
covering .mxl container resolution, SATB part extraction, key/meter maps,
divisions→beats conversion, chord onsets, backup/forward cursor movement,
spelling metadata, and empty tempoMap when no tempo direction exists.

## Behaviors to verify (remaining)

- **Parser boundary conformance (from #16 spec):** `validateIR(parserOutput)`
  returns zero errors and `normalizeIR(parserOutput)` is idempotent — the
  chorale fixture already implies this (parser throws on invalid IR), but pin
  idempotence explicitly alongside the MIDI boundary check (#17).
- **Timewise input:** parser currently rejects `score-timewise` (pinned by
  test). If timewise support is ever wanted, that's a scope decision for the
  human — the rejection is the pinned behavior until then.
- **Non-traditional key signatures** (`key-step`/`key-alter` lists) and
  composite time signatures with multiple beat-types are currently skipped
  (no IR entry) — pin that they don't crash the parser; formal support is a
  spec question.
- **Mode mapping:** only fifths=1/G major is exercised. Add parameterized
  cases across the circle of fifths × modes (dorian, mixolydian, minor) if
  `keyFromSignature` ever drifts.
- **Measure-boundary beats:** multi-measure rests and `<forward>` across
  measure boundaries — current tests cover in-measure forward only.

## How to run

`npm test` (picks up `tests/musicxml.test.mjs` automatically), or standalone:
`node tests/musicxml.test.mjs`.
