# Test spec — Batch 1 #4: metadata.schema.json

**Source task:** #4 (metadata.schema.json)
**Code under test:** `schema/metadata.schema.json` via `tools/validate.mjs`

## Behaviors to verify

- Valid doc with a 26-char Crockford-base32 ULID `id` validates.
- Valid doc with a UUID `id` validates.
- `license.renditions` outside the enum (`presets-only | open-within-constraints | closed`) rejected.
- Missing any required top-level field (`id`, `title`, `composer`, `created`, `license`, `provenance`) rejected.
- Malformed `id` (wrong length / excluded chars I, L, O, U) rejected.
- `created` not RFC 3339 date-time rejected.
- Unknown top-level property rejected (`additionalProperties: false`).
- `provenance` item missing `event` rejected.
- Optional fields (`composer.id`, `license.attribution`, `license.commercial`, provenance `at`/`ai`/`notes`) may be absent without failing.

## Edge cases

- ULID vs UUID boundary: exactly-26 ULID passes, 25-char fails.
- `composer.name` empty string rejected (`minLength: 1`).

## How to run

Fold into the `npm test` harness (#3) as a `metadata` fixture pair (valid + one invalid
per case above). Reference implementation used during authoring: per-case `node
tools/validate.mjs <fixture> schema/metadata.schema.json` — all passed.

## Coverage landed (issue #28)

`tests/metadata.test.mjs` — 25 cases covering every behavior and edge case in
this spec: ULID/UUID acceptance, 25/27-char and excluded-char (I/L/O/U) id
rejection, license.renditions enum, each required field, RFC 3339 created,
empty title/composer.name, additionalProperties strictness (top-level and
license), provenance item event requirement, optional-field absence.
Run via `npm test` (harness folds in all `tests/*.test.mjs`) or
`node tests/metadata.test.mjs` standalone.
