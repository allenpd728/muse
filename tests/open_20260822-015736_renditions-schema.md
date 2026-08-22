# Test spec — Batch 1 #9: renditions.schema.json

**Source task:** #9 (JSON Schema for the `renditions` block, spec §2.6)
**Code under test:** `schema/renditions.schema.json`
**Already covered:** `tests/renditions.test.mjs` (folds into `npm test`) — both
spec §2.6 examples validate; missing/empty id and name rejected; density/tempo
bounds; `additionalProperties: false` at rendition/style/author level.

This spec covers what that suite does not.

## Behaviors to verify

- `params.swing` bounds (0–1) pinned by a test — suite covers density and
  tempo_bpm but not swing.
- `style` and `params` are each optional as a whole, but if present must be
  objects (e.g. `"style": "synthwave"` rejected).
- `style.references` entries must be non-empty strings; non-string entries
  (e.g. numbers) rejected.
- `instrumentation` entries must be non-empty strings.
- Root must be an array: a single rendition object (not wrapped) is rejected.
- Non-object items inside the array (string, null) rejected.
- `era` is a string in the spec examples ("1984"); pin whether a numeric era
  (1984) is rejected (current schema: yes) — if a real use case wants numbers,
  that is a spec question, not a schema bug.
- Compose check: once #11 lands the root schema, a document whose `renditions`
  violates this schema fails validation through `schema/muse.schema.json`
  (proves the `$ref` wiring, not just the standalone file).

## Edge cases

- The §2.6 hard rule (no named-artist references without a license record) is
  **semantic** — JSON Schema cannot enforce it. Nothing to test mechanically;
  flag for the future lint/conformance layer, and confirm here that the schema
  deliberately does not try (e.g. a genre-named string in `references` passes).
- Duplicate rendition ids within one array — not enforceable in draft 2020-12;
  note as a candidate for the code-level xref/lint pass alongside material ids.

## How to run

Add cases to `tests/renditions.test.mjs` (or a new `tests/*.test.mjs` file);
the harness (`npm test`) picks up every `tests/*.test.mjs` automatically.
