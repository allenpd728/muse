# Test spec — Batch 1 #5: globals.schema.json

**Source task:** #5 (JSON Schema for the `globals` block, spec §2.2)
**Code under test:** `schema/globals.schema.json`; suite `tests/globals.test.mjs`
(runs standalone and under `npm test` via the `tests/*.test.mjs` fold-in).

The task's own suite already covers the definition of done (simple + additive
meter valid; inverted ranges rejected). This spec captures the residual
coverage not possible until dependent tasks land.

## Behaviors to verify (already in `tests/globals.test.mjs`)

- Spec §2.2 snippet end-to-end valid.
- `meter.beats` as integer (simple) or array of 2+ integers (additive); both
  valid; `beats: 0` rejected.
- `key`: named tonic requires `mode`; `{tonic: "atonal"}` needs no mode.
- `tempo` requires `bpm`; unknown globals members rejected
  (`additionalProperties: false` decision).
- Inverted `tempo.range` ([112, 84]) is structurally valid to the schema but
  rejected by the semantic ordering check **(code, not ajv)**.

## Residual coverage this follow-up must add

- **Root-schema integration:** once #11 (`schema/muse.schema.json`) lands,
  validate `globals` through the root `$ref` — currently the section schema is
  compiled standalone.
- **Semantic range lint:** fold range-order checking into the harness lint
  step alongside cross-refs (currently implemented ad hoc in the test file).
- **Edge cases:** `beats` as a 1-element array (minItems: 2 rejects — pin
  intent), non-power-of-2 `unit` (schema intentionally allows; pin intent),
  `tempo.range` with equal bounds (allowed — a fixed tempo).

## How to run

`node tests/globals.test.mjs` or `npm test`.

## Notes

JSON Schema draft 2020-12 cannot compare two data values, so range ordering
(min ≤ max) is a semantic check — same class as the harness's cross-reference
lint. Keep it in code; do not block the schema task on it.
