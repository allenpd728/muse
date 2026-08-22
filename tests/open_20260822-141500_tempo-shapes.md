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
