# Test spec — Batch 1 #13: full example

**Source task:** #13 (examples/full.muse.json)
**Code under test:** `examples/full.muse.json` against `schema/muse.schema.json` + harness cross-refs

## Behaviors to verify

- `examples/full.muse.json` validates against the root schema (`npm test` includes it once harness scans examples/).
- Cross-reference integrity holds: every `form.sections[].uses[].ref` (incl. transform-suffixed) and `harmony` ref, and every `constraints.must_contain` id, resolves to a defined material id.
- The document exercises every top-level section (metadata, globals, material, form, constraints, renditions, extensions) — guards against silent section regressions.

## Notes

Authored with an additive meter `[3,3,2]` and both spec §2.6 renditions to stress the seams.
During authoring the validator caught an invalid ULID `metadata.id` — evidence the harness is load-bearing. If the example later fails on id, suspect the ULID/UUID pattern first.

## Coverage landed (closed 2026-08-22)

`tests/full-example.test.mjs` (15 assertions, folded into `npm test`):
root-schema validation via the real CLI; all 8 top-level sections present;
harness danglingRefs clean; theme phrase motif refs resolve with transform
suffixes stripped; constraints register/tempo_lock keys resolve to material/
section ids; form.order + repetition keys name defined sections; the
form-used-theme-contains-must_contain-motif seam join.

Run: `npm test` (suite folds into the harness's tests/*.test.mjs scan).
CI execution is inherited from the workflow's `npm test` step — first green
run still pending the account billing unlock tracked in #42's blocker
(`blockers/open_20260822-102800_ci-billing-lock.md`).

## How to run

`npm test` (once #12/#14 land the examples scan). Reference: `node tools/validate.mjs examples/full.muse.json` — valid at authoring, harness 12/12 green.
