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

## How to run

`npm test` (once #12/#14 land the examples scan). Reference: `node tools/validate.mjs examples/full.muse.json` — valid at authoring, harness 12/12 green.
