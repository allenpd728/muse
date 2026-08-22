# Test spec — Batch 1 #12: examples/minimal.muse.json

**Source task:** #12 (smallest valid Muse document)
**Code under test:** `examples/minimal.muse.json` against
`schema/muse.schema.json` (root, via `tools/validate.mjs` / `npm test`).

## Behaviors to verify

- `examples/minimal.muse.json` validates against the root schema and passes
  the harness's example loop (already live: the `mustPass` glob picked it up
  the moment the file landed — pinned by `npm test` on every run).
- Removing any root-required field (`muse_version`, `metadata`, `globals`)
  fails validation — verified manually at authoring via
  `node tools/validate.mjs <mutated>`; worth automating as a mutation test in
  the harness or a `tests/minimal.test.mjs` suite.
- `metadata.provenance` entry present with `ai: true` per the project's
  provenance rule — the schema requires the `provenance` array; pinning that
  minimal.muse.json specifically carries an AI disclosure needs a code check
  (ajv can't assert project policy).
- Document stays minimal: no `material`/`form`/`constraints`/`renditions`/
  `extensions` — guard against the example accreting sections that belong in
  `examples/full.muse.json` (#13). A lint asserting "minimal ⊂ required only"
  belongs in the harness or CI.

## Edge cases

- `muse_version` must remain a valid semver string per the root pattern.
- `globals` is present but sparse (`tempo.bpm`, `meter`, `duration_bars`
  only) — adding `key` or `tempo.range` is allowed by the schema but changes
  the example's intent; flag in review, not schema.

## How to run

`npm test` (harness example loop), or directly:
`node tools/validate.mjs examples/minimal.muse.json` (exit 0; removing a
required field → exit 1).
