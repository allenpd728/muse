# Test spec: performance JSON Schema residual coverage (follow-up to #22)

**Source task:** #22 (schema/performance.schema.json)
**Code under test:** `schema/performance.schema.json` + `tests/performance.test.mjs`
`perfRefs()` lint (DoD: hand-built fixture validates, out-of-range velocity and
dangling part refs rejected). This spec covers what remains.

## Behaviors to verify

- **Duplicate part ids**: two parts sharing an id — reference resolution is
  ambiguous; pin either a duplicate-id lint rule or document the Set-based
  resolution as-is (mirrors the section-id question in form).
- **tempo_map ordering**: the player interpolates between points — unsorted
  entries pass the schema today. If ordering matters to #24's player, pair
  this with a normalize/lint rule; otherwise pin that arbitrary order is
  accepted.
- **mix partials**: a `mix` object with only `gain` (no `pan`/`reverb_send`)
  validates; one with an unknown member rejected.
- **dynamics global vs part-tagged**: both forms in one array (already in the
  fixture; pin explicitly).
- **controllers unknown member**: rejected under the sealed controller object.
- **notes off-part**: `onset_beat`/`duration_beats` optional-to-present but
  `onset`/`duration` (seconds) always required — pin that a beats-only note
  is rejected (seconds are authoritative).

## How to run

Extend `tests/performance.test.mjs`; `npm test`.

## Resolution

Residual coverage landed in `tests/performance-residual.test.mjs` (issue #64):
duplicate part ids pinned (Set-based resolution; dup detection is not a lint
rule), mix partials (gain-only valid, unknown member rejected), dynamics
global+part-tagged coexistence, and the seconds-authoritative pin (beats-only
note rejected). tempo_map ordering and controllers-unknown were already
covered in the #62 pass. 9/9 standalone; npm test green.
