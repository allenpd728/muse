# Test spec — Batch 1 #2: validator CLI

**Source task:** #2 (package scaffolding + validator CLI)
**Code under test:** `tools/validate.mjs`

## Behaviors to verify

- Valid document → prints `valid: <name>`, exit 0.
- Missing required property → prints `invalid:` + ajv error path, exit 1.
- Wrong type for a known property → readable error, exit 1.
- Missing/unparseable document file → error message, exit 1 (no stack trace).
- Malformed schema file → `schema error:` message, exit 1.
- No document argument → usage message, exit 1.
- Default schema path (`schema/muse.schema.json`) is used when the schema arg is omitted.
- Relative `$ref` between schemas resolves once section schemas land (placeholder: assert the CLI compiles a schema that `$ref`s a sibling file).

## Edge cases

- Document with extra/unknown properties (placeholder schema does not set `additionalProperties:false` — confirm intended behavior once section schemas define it).
- Empty JSON object `{}` against a schema with `required`.
- Non-JSON input (e.g. plain text file).

## How to run

`node tools/validate.mjs <doc> [schema]` directly, or via the future test harness
(`npm test`, Batch 1 #3). These cases fold into that harness's valid/invalid
assertions.

## Notes

ajv draft 2020-12 support comes from `ajv/dist/2020.js`; a regression to plain
`ajv` import surfaces as "no schema with key or ref .../2020-12/schema" — pin
that in a test.

## Resolution

Landed in `tests/validate-cli.test.mjs` — 10 cases, all passing (`node tests/validate-cli.test.mjs`). Covers valid/missing-required/wrong-type/non-JSON/missing-file/malformed-schema/no-arg/empty-object/unknown-props/default-schema-path. Folds into the #3 harness when it lands.
