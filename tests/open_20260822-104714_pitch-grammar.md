# Test spec — Fix #44: shared pitch grammar

**Source task:** #44 (pin a shared pitch grammar for motif pitches and register bounds)
**Code under test:** `schema/material.schema.json` `$defs/pitch`, referenced from
`material.motifs[].pitches` and `constraints.register` bounds.

Partial coverage landed with the task: `examples/invalid/bad-pitch-grammar.muse.json`
proves rejection of `"banana"` (motif pitch) and `"42"` (register bound) via the
harness `mustReject` loop, and existing examples prove acceptance of
`D4/F4/A4/G4/C4/A5`. This spec is for the coverage that remains.

## Behaviors to verify

- Acceptance: all seven naturals, sharps (`F#4`), flats (`Bb3`), negative
  octave (`C-1`), double-digit octave (`C10` — grammar pins form, not the
  MIDI 0-127 range; range semantics are an engine concern).
- Rejection: lowercase letter (`c4`), double accidental (`F##4`), missing
  octave (`F#`), octave-only (`4`), empty string, `H4` (non-German
  convention; if German notation is ever wanted it is a spec amendment).
- Grammar applies only where pitches are present: rhythm/timbre motifs
  without `pitches` still validate (already pinned by material tests; keep).
- Cross-file `$ref` integrity: `constraints.schema.json` compiled standalone
  resolves `material.schema.json#/$defs/pitch` (the `addSchema` pre-register
  in `tests/constraints.test.mjs` covers this — assert it stays wired if the
  validator's sibling-registration changes).
- Parity with `importer/ir.mjs` `pitchToMidi` grammar: the schema pattern and
  the importer's `PITCH_RE` accept the same language. A table-driven test
  over ~20 pitch strings asserting schema-valid ⇔ importer-parses would pin
  the two grammars to each other.

## How to run

Fold into `tests/material.test.mjs` / `tests/constraints.test.mjs` (accept/reject
tables) plus the parity suite as `tests/pitch-grammar.test.mjs`; `npm test`.
