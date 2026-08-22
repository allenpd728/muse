# Test spec — Batch 3 #22: performance-layer JSON Schema

**Source task:** #22 (schema/performance.schema.json)
**Code under test:** `schema/performance.schema.json`, `checkPerfRefs()` in
`tools/semantics.mjs`, fixture `tools/fixtures/valid.muse.perf.json`.

DoD coverage landed with the task: `tests/performance.test.mjs` — 24 checks
(hand-built doc validates via ajv and the CLI; velocity out-of-range
rejected; dangling part refs flagged on both surfaces; shape invariants).
This spec is for what remains.

## Behaviors to verify

- **Harness integration decision (open):** perf docs currently bypass the
  `tools/test.mjs` example loops by suffix design (`*.muse.perf.json`).
  Decide whether the harness gains a perf channel (mustPass/mustReject over
  a perf-examples dir, wiring `checkPerfRefs` like `danglingRefs`) before
  #23/#24 land fixtures — or the CLI + suite contract stays the pin.
- **§7 example ⇔ schema conformance:** the spec §7 jsonc example parses and
  validates against `performance.schema.json` (transfers the #61 scope-guard
  idea to the executable schema).
- **Clock consistency (semantic, future):** onset/duration seconds agree
  with onset_beat/duration_beats under the tempo_map — a semantic check
  once the interpreter (#23) emits real docs; pin tolerance policy there.
- **tempo_map ordering + interpolation domain:** sorted by time, player
  interpolation defined between points — pin once #24 consumes it.
- **Renderer-declared controllers vs schema:** #24's renderer contract
  intersects `controllers` keys — pin that unknown controller names stay
  rejected (sealed) or move to an open set by deliberate spec edit.

## How to run

`npm test`; new suites as `tests/*.test.mjs`.
