# Test spec — #75: constraints.tempo_shapes (v0.3)

**Source task:** #75 (schema v0.3: rubato/tempo-modification semantics)
**Code under test:** `schema/constraints.schema.json` (`tempoShape` $def);
`SCHEMA_SPEC.md` §2.5; `examples/full.muse.json`.

Baseline coverage landed with the task: `tests/constraints.test.mjs` — 12
checks covering all three kinds, required-field conditionals
(target_bpm for rit./accel., deviation_bpm for rubato), sealed objects,
unknown kind/span rejection, and composition with `tempo_lock`.

## Behaviors to verify (remaining)

- **Performance-layer conformance (needs #72 metrics harness or interpreter
  tests):** a performance `tempo_map` realizing a `tempo_shapes` constraint
  is checkable — rit./accel. produce a monotone ramp ending at `target_bpm`
  within the span; rubato stays within the deviation band and returns to the
  section base tempo. This is the semantic half of the contract; the JSON
  Schema pins syntax only.
- **Spec ↔ schema parity:** the three kinds and span enum in SCHEMA_SPEC.md
  §2.5 match `schema/constraints.schema.json` (same inspection pattern as
  the role-vocabulary parity pin in #69).
- **Example retains the shape:** `examples/full.muse.json` keeps its
  `bridge.cadenza` ritardando (guards against example edits silently
  dropping the construct — mirrors the role guard).
- **Interpreter prompt** (Batch 3 #23 lineage) honors `tempo_shapes` when
  generating `tempo_map` — belongs to interpreter tests; flagged here so it
  doesn't fall between the seams.

## How to run

`npm test` (syntax pins live in `tests/constraints.test.mjs`); semantic
conformance checks land with #72 or interpreter test follow-ups.

---

## Closed — 2026-08-22 (issue #84)

Coverage landed:

- **Performance-layer conformance:** `tempoShapeConformance()` in
  `benchmark/metrics.mjs` — rit./accel. require a monotone ramp ending at
  `target_bpm` within the section span; rubato requires deviation within
  the band and return to base tempo at section end. Wired into
  `scorePerformance` as the `tempo_shapes` report field. 9 new checks in
  `tests/benchmark.test.mjs` (both ramp kinds, target-not-reached,
  non-monotone, rubato band/return failures, vacuous case) + the full
  example's cadenza ritardando scored conformant end-to-end.
- **Interpreter honors tempo_shapes:** the offline expander
  (`interpreter/offline.mjs`) now realizes `constraints.tempo_shapes` into
  the perf `tempo_map` (rit./accel. ramp to target within span; rubato
  triangle within band, returning to base). The LLM prompt path inherits
  the semantic through the constraint summary; pinning its adherence is
  live-model smoke (see #65's closed spec).
- **Spec ↔ schema parity + example retention:** pinned by the existing
  conventions and constraints suites (kinds/span enums unchanged since
  #75; `bridge.cadenza` ritardando asserted conformant in the e2e check).

Run: `npm test`.
