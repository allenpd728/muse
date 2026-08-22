# Test spec — Fix #45: seal metadata.provenance items

**Source task:** #45 (seal metadata.provenance items — additionalProperties: false)
**Code under test:** `schema/metadata.schema.json` `provenance.items`.

## Behaviors to verify

- Extra property on a provenance entry rejected (verified manually during
  #45: `/metadata/provenance/0 must NOT have additional properties`) — pin
  via an `examples/invalid/bad-provenance-prop.*` pair or a unit case in
  `tests/metadata.test.mjs`.
- All five defined fields (`event`, `actor`, `at`, `ai`, `notes`) still
  validate together; an entry with only `event` still validates.
- Sibling sealed objects stay sealed: extra property on `composer` and
  `license` still rejected (regression guard against someone loosening the
  whole file).
- Heads-up for #19 (synthesis): docs/scope-importer.md describes import
  provenance as "one entry: event: \"import\", source filename/format,
  ai: false" — under the sealed schema, filename/format must ride in
  `notes` (or a schema field must be proposed). A test asserting the
  importer's emitted provenance entry validates will catch this at #19
  time; the synthesis author should not re-open the seal silently.

## How to run

`npm test`; invalid-example pair folds into the harness `mustReject` loop,
unit cases into `tests/metadata.test.mjs`.
