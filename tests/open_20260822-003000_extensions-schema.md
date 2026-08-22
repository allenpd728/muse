# Test spec — Batch 1 #10: extensions.schema.json

**Source task:** #10 (extensions.schema.json)
**Code under test:** `schema/extensions.schema.json` via `tools/validate.mjs`

## Behaviors to verify

- Spec §2.7 example (`{"engine.audiocraft": {"cfg": 3.5}}`) validates.
- Empty `{}` validates.
- Multiple namespaces validate; arbitrary content types (object, array, string, nested) validate.
- Uppercase / invalid namespace key rejected (`propertyNames` pattern).
- Non-object root rejected.

## How to run

Fold into the `npm test` harness (#3) as fixtures. Reference per-case checks via
`node tools/validate.mjs <fixture> schema/extensions.schema.json` — 8/8 passed at authoring.
