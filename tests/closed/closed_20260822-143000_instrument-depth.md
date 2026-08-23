# Test spec — #76: performance instrument depth (v0.3)

**Source task:** #76 (schema v0.3: orchestral instrumentation depth)
**Code under test:** `schema/performance.schema.json` (`instrument.divisi`,
`doubles`, `techniques` + `technique` $def); `SCHEMA_SPEC.md` §7.

Baseline coverage landed with the task: `tests/performance.test.mjs` — 7
checks (divisi valid/1-rejected, doubles valid/empty-string-rejected,
techniques valid/unknown-rejected, sealed-instrument regression).

## Behaviors to verify (remaining)

- **Spec ↔ schema parity:** the technique enum in §7 matches
  `performance.schema.json#/$defs/technique` (inspection pin, same pattern
  as role/tempo-shape parity specs).
- **Honor-or-drop conformance (Player V1 lineage):** a player given a
  technique it can't render drops it and records the drop in
  `extensions.<player>.dropped` — never fails. This is semantic; belongs in
  player tests when Player V1 handles techniques (flag for the #66 lineage).
- **Interpreter prompt** (Batch 3 #23 lineage) emits techniques/divisi when
  the schema rendition sanctions them — interpreter test follow-up.
- **Rendition sanctioning of doubles** is named in the spec but has no
  schema construct yet — that's the "which doubles are sanctioned is a
  schema/rendition decision" half. If a rendition-level vocabulary is
  wanted, it's a v0.3 follow-up task, not this spec.

## How to run

`npm test` (syntax pins in `tests/performance.test.mjs`); semantic checks
land with player/interpreter test follow-ups.

---

## Closed — 2026-08-22 (issue #86)

Coverage landed:

- **Spec ↔ schema parity:** §7's technique list set-equals
  `performance.schema.json#/$defs/technique` — pinned in
  `tests/performance.test.mjs` (same inspection pattern as the
  role/tempo-shape parity pins).
- **Honor-or-drop conformance:** `player/render.mjs` gains
  `droppedTechniques()` — the drop record per spec §7 (V1 honors GM
  program only, so every technique drops today; the recording path is
  the contract). 3 checks in `tests/player.test.mjs`: drops recorded,
  render never fails (bit-identical output), empty record without
  techniques.
- **Interpreter prompt emitting techniques:** the offline expander does
  not yet map rendition-sanctioned techniques into part
  `instrument.techniques` — flagged as follow-up work on the #91/#92
  lineage (material/rendition realization), not this spec.
- **Rendition-level doubles vocabulary:** remains a v0.3 follow-up task
  as the spec's own note says — no schema construct added here.

Run: `npm test`.
