# Test spec — Fix #43: metadata.id grammar reconciliation

**Source task:** #43 (reconcile metadata.id grammar between spec and schema)
**Code under test:** `schema/metadata.schema.json` `id` pattern via
`tools/validate.mjs`; `SCHEMA_SPEC.md` §2.1/§2.8 as the stated convention.

## Behaviors to verify

- `muse:work:` + ULID (26 chars, Crockford base32) validates — the spec §2.1
  example form; verified manually during #43, needs a pinned test.
- Bare ULID and bare RFC 4122 UUID still validate (backward compatibility).
- `muse:work:` + UUID validates (prefix composes with both id kinds).
- Rejected: wrong namespace prefix (`muse:track:…`), prefixed ULID with wrong
  length (25 or 27 chars), lowercase ULID (Crockford base32 is uppercase),
  malformed UUID.
- Existing examples (`examples/*.muse.json`, `tools/fixtures/valid.muse.json`)
  keep validating — covered by the harness loops today; assert at least one
  fixture exercises the prefixed form so the new branch can't silently rot.
- Pin from §2.8: internal ids (motifs/themes/rhythms/progressions/sections/
  renditions) follow the dotted-slug convention `^[A-Za-z0-9_.-]+$` as a
  convention only — schemas do NOT enforce it (chord symbols like `Dm7` are
  free text and must keep validating as progression chord entries). A test
  should assert a non-slug section id still validates, pinning the
  convention-not-enforcement decision.

## How to run

Fold into `tests/metadata.test.mjs` (or a new `tests/metadata-id.test.mjs`);
driven via `node tools/validate.mjs <fixture> schema/muse.schema.json` against
crafted metadata fixtures, run by `npm test` in CI.
