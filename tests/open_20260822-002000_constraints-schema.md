# Test spec — Batch 1 #8: constraints.schema.json

**Source task:** #8 (constraints.schema.json)
**Code under test:** `schema/constraints.schema.json` via `tools/validate.mjs`

## Behaviors to verify

- Full spec §2.5 example validates.
- Empty `{}` validates (all blocks optional).
- `must_contain` entries must be non-empty strings.
- `must_not` predicate missing `kind` rejected.
- `modulation_beyond` predicate requires `semitones`; `semitones: 0` or negative rejected.
- Unknown `must_not` predicate kinds are preserved (validate) — extensibility contract.
- `tempo_lock` values are 2-element [min,max] bpm ranges; one-element rejected; `0` bpm rejected.
- `register` values are 2-element [low, high] pitch pairs; one-element rejected.
- `structure.form_deviation` outside `none|reorder|abridge` rejected.
- Unknown top-level property rejected (`additionalProperties: false`).

## How to run

Fold into the `npm test` harness (#3) as fixtures. Reference per-case checks via
`node tools/validate.mjs <fixture> schema/constraints.schema.json` — 14/14 passed at authoring.
