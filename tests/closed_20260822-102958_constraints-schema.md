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

## Resolution

Coverage landed in `tests/constraints.test.mjs` (issue #33): all 14 spec cases
plus boundary extras (three-element tempo_lock/register arrays, negative bpm,
non-string must_contain entry, unknown member in `structure`). 19/19 pass
standalone (`node tests/constraints.test.mjs`) and under `npm test`, where the
harness picks the file up automatically and CI runs it on push to dev.
