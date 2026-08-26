# Test spec — S3.7 lineage fields on seed provenance (task #248)

Written 2026-08-25 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

`tools/muse_seed/seed.py` `_validate_provenance()`, wired into
`validate_seed()`: optional `provenance.extends` (must be a bare 64-hex
SHA-256 string when present) and `provenance.operation` (must match
`tool@version`: `^[a-z][a-z0-9_]*@\d+(\.\d+)*$`). All other provenance
keys remain free-form. Spec entry: `docs/design/s3-seed-format/SPEC.md`
decisions log ("Lineage fields (S3.7, 2026-08-25, #248)").

## Coverage to write

Target file: `tools/muse_seed/test_lineage.py` (new), run with
`cd tools && python -m pytest muse_seed -q`.

1. **Acceptance.** A valid seed dict passes with: no lineage fields;
   `extends` only; `operation` only; both. Round-trip through
   `load_seed`/`dump_seed` preserves both fields.
2. **`extends` rejection.** Too short, too long (65 chars), non-hex
   characters, `sha256:`-prefixed digest (the prefix is NOT the
   convention — regression-pin this), non-string value (int, list).
3. **`operation` rejection.** Capitalized tool (`Distill@1`), missing
   version (`muse_distill`), missing tool (`@1`), space in name,
   non-numeric version (`@x`). Accepts `muse_distill@1` and
   `muse_author@1.2.3` (both shapes are sanctioned).
4. **Non-breaking pin.** All committed seeds under `seeds/` validate
   unchanged (none carry the fields today).
5. **CLI seam.** `muse_seed_cli validate` exits 1 with a malformed
   `extends` in the seed file (message names `provenance.extends`).

## Known gaps (acceptable)

- Cross-artifact chain *verification* (does `extends` actually match a
  real parent's bytes) is S3.8a (#251), not this task — no test here
  should attempt it.
- The manifest-side mirror (S5.1, #249) has its own test spec.

## Closed 2026-08-26 (#255, run=20260825-1033-cae1)

Landed in `tools/muse_seed/test_lineage.py` (22 tests):

1. **Acceptance:** no-fields / extends-only / operation-only / both;
   both fields round-trip through load/dump in YAML and JSON.
2. **extends rejection:** short/long/non-hex/`sha256:`-prefixed
   (regression-pinned as NOT the convention)/non-string/list. One spec
   adjustment: uppercase hex is *accepted* — `is_sha256_hex` documents
   "lowercase-or-upper" as the manifest's shape; the rejection case
   became an acceptance pin.
3. **operation rejection:** capitalized tool, missing version, missing
   tool, space, non-numeric version, non-string; both sanctioned shapes
   (`@1`, `@1.2.3`) accepted.
4. **Non-breaking pin:** all 3 committed seeds validate unchanged.
5. **CLI seam:** malformed `extends` → `_validate` exit 1 naming the
   field.
