# Test spec — Batch 1 #6: material.schema.json

**Source task:** #6 (material.schema.json)
**Code under test:** `schema/material.schema.json` via `tools/validate.mjs`

## Behaviors to verify

- Full spec §2.3 example document validates (motif with pitches/durations/contour/tags, theme with transform refs, rhythm with grid, harmony with progression + vocabulary).
- Empty `{}` validates (all sub-objects optional).
- `motifs[].kind` outside enum (`pitch|rhythm|pitch_rhythm|timbre|harmonic`) rejected.
- Motif missing required `kind` rejected.
- Unknown top-level property rejected (`additionalProperties: false`).

## Transform references (`motifRef`)

- Plain id `motif.a` valid.
- Each transform valid: `#seq(+2)`, `#seq(-1)`, `#inv`, `#retro`, `#aug(2)`, `#dim(0.5)`.
- Chained transforms valid: `motif.a#retro#aug(2)`.
- Unknown transform `#bogus` rejected; bare `#inv` (no id) rejected.

## Edge cases

- `durations` entry of `0` rejected (`exclusiveMinimum: 0`); negative rejected.
- `rhythms[].pattern` entry negative rejected (`minimum: 0`); `0` allowed (rest).
- `bars_per_chord` of `0` rejected.

## How to run

Fold into the `npm test` harness (#3) as fixtures. Reference per-case checks via
`node tools/validate.mjs <fixture> schema/material.schema.json` — all passed at authoring.

---

## Closed — 2026-08-22 (issue #29)

Coverage landed as `tests/material.test.mjs` (21 checks, folded into `npm test`
via the `tests/*.test.mjs` fold-in): full spec §2.3 example, empty-object and
top-level strictness, `kind` enum + required, the complete `motifRef` transform
grammar (each transform, chained transforms, `#bogus`/bare-`#inv` rejection),
and the numeric edges (`durations` 0/negative, `pattern` rest-0 vs negative,
`bars_per_chord` 0). Every behavior in the spec above is covered; no residue.

Run: `node tests/material.test.mjs` or `npm test`.
