# Test spec — #67: schema v0.2 section-role vocabulary

**Source task:** #67 (broaden `form.sections[].role` beyond pop structure)
**Code under test:** `schema/form.schema.json` role enum; `SCHEMA_SPEC.md` §2.4; `examples/full.muse.json`.

Baseline coverage landed with the task: `tests/form.test.mjs` iterates all 33
enum values (accepted) plus `ritornello` as an unknown-role rejection canary.

## Behaviors to verify (remaining)

- **Spec ↔ schema parity:** the role list in SCHEMA_SPEC.md §2.4 and the enum
  in `schema/form.schema.json` stay in sync — codify by parsing the spec's
  backtick-quoted role tokens from §2.4 and asserting set-equality with the
  schema enum (same pattern as conventions.test.mjs schema inspection).
- **Cross-tradition example:** `examples/full.muse.json` retains at least one
  section whose role is outside the song-form group (currently `cadenza`) —
  guards against example edits quietly reverting to pop-only vocabulary.
- **Explorer pass-through:** the explorer renders an arbitrary new role
  without code changes (it reads `s.role` verbatim today — pin with a fixture
  or component-level check if/when the explorer gets a test story; not
  covered by root `npm test` per the explorer package decision).
- **Downstream consumers:** importer synthesis (#19) emits role `custom` by
  default — confirm imported documents still validate (they do; pin a
  synthesis fixture asserting the emitted role is in the enum).

## How to run

`npm test` (schema/example pins), or `node tests/form.test.mjs` standalone.
Explorer check belongs to a future explorer test suite.
