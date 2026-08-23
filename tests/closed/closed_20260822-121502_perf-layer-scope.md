# Test spec — Batch 3 #21: performance-layer scope doc

**Source task:** #21 (docs/scope-batch3.md + spec §7 draft)
**Code under test:** documents — `docs/scope-batch3.md`, SCHEMA_SPEC.md §7.
No code shipped; coverage is consistency guards against the formats they pin.

## Behaviors to verify

- **§7 example conforms to the scope doc shape** (and vice versa): parse the
  §7 jsonc example (strip comments/trailing commas) and assert the documented
  required fields exist — `muse_perf_version`, `metadata.source`,
  `metadata.interpreter`, `tempo_map`, `parts`, `notes`; `notes[]` entries
  carry both clocks (`onset`/`duration` seconds + `onset_beat`/
  `duration_beats`); `pitch_name` in the example matches the §2.3 pitch
  grammar (`^[A-G](?:#|b)?-?\d+$`).
- **`*.muse.perf.json` does not collide with the harness example glob:**
  assert a path like `examples/invalid/x.muse.perf.json` would NOT match the
  harness's `*.muse.json` filter (pin the suffix decision so a future rename
  can't silently pull perf docs into the schema-example loops).
- **Renderer contract documented:** scope doc contains `capabilities` and
  `render` signatures (grep-level guard against silent contract drift;
  #22/#24 supersede this with real schemas/tests as they land).
- **Versioning discipline:** `muse_perf_version` in the §7 example matches
  the semver pattern from `schema/muse.schema.json` — one regex source,
  reused, not re-invented.

## How to run

`tests/perf-scope.test.mjs` (or fold into `tests/conventions.test.mjs`);
`npm test` picks it up. Superseded in part by #22 (`performance.schema.json`
makes the shape executable) — whichever lands first, the consistency guard
between §7's example and the schema stays.
