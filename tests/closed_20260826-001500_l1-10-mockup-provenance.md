# Test spec — L1.10 mockup provenance.seed_hash (task #250)

Written 2026-08-26 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

`tools/muse_mockup/schema/v1.json`: optional `provenance` object with
`seed_hash` (bare 64-hex, S3.7/#248 convention); the vestigial optional
`"seed"` property deleted. `tools/muse_mockup/schema.py`
`validate_mockup_schema()` validates `provenance` (dict) and
`seed_hash` (via `muse_seed.seed.is_sha256_hex` — the shared convention)
when present. Baseline coverage shipped with the change:
`test_provenance_seed_hash` in `tools/muse_mockup/test_mockup_schema.py`.

## Coverage to write

Extend `tools/muse_mockup/test_mockup_schema.py`, run with
`cd tools && python -m pytest muse_mockup -q`.

1. **Round-trip seam.** `dump_mockup()` → `load_mockup()` preserves a
   `provenance.seed_hash` attached to a mockup dict (pin whether the
   model carries provenance at all — if the `Mockup` dataclass doesn't,
   that gap is a finding to report, not paper over; the schema field is
   for the session file on disk).
2. **Rejection matrix.** `seed_hash`: short/long, non-hex, upper- vs
   lowercase hex (pin accepted case behavior — `is_sha256_hex` accepts
   both, matching the manifest), non-string. `provenance` non-dict.
   Prefixed `sha256:` value rejected (regression pin).
3. **Additivity pin.** A mockup dict with `provenance` carrying extra
   keys beyond `seed_hash` (e.g. a future `run_id`) still validates —
   the typed-provider series will add those fields and must not be
   blocked by this validator.
4. **Schema/validator parity.** The `pattern` in v1.json and
   `is_sha256_hex` agree on a shared input matrix (the two are separate
   enforcement layers; drift between them is a real failure mode).

## Known gaps (acceptable)

- Nothing *writes* `seed_hash` yet — the L1 generate loop (real) and
  S3.8b (#254, mockup persistence) are the producers. Tests here cover
  the schema/validator contract, not generation.

## Closed 2026-08-26 (#257, run=20260825-1033-cae1)

Extended `tools/muse_mockup/test_mockup_schema.py` (+5 tests, suite 22 →
27):

1. **Round-trip seam (item 1, reported as instructed):** the `Mockup`
   dataclass does NOT carry provenance — dump/load silently drops it.
   Pinned as a flip-test (`test_round_trip_seam_reports_dataclass_gap`):
   when Mockup grows provenance serialization, the test fails and must be
   inverted. The schema field serves the session file on disk.
2. **Rejection matrix:** short/long/non-hex/non-string/list +
   `sha256:`-prefixed (regression pin) all rejected; both hex cases
   accepted (parity with the manifest convention).
3. **Additivity pin:** extra provenance keys (run_id, provider) validate
   alongside seed_hash — the typed-provider series is not blocked.
4. **Schema/validator parity:** v1.json's regex pattern and
   `is_sha256_hex` agree on a shared 8-input matrix.
