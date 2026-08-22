# Test spec — Composer MVP 5 #83: validation + export

**Source task:** #83 (inline error surfacing, download .muse.json, load
existing file, export provenance entry)
**Code under test:** `explorer/src/composer/main.jsx`
(withExportProvenance, download, error panel).

Coverage landed with the task: `explorer/src/composer/export.test.mjs` —
5 vitest checks (provenance shape, schema-legality, immutability,
double-export, error surfacing contract) plus a browser pass (export
button + clean panel on the full example). This spec is for what remains.

## Behaviors to verify

- **Download round-trip through the browser:** export → file → reload into
  the composer → doc equality (scripted browser; the download helper
  itself is a thin Blob wrapper, untestable in vitest).
- **Export filename:** derived from the loaded doc name with `.muse.json`
  suffix — pin sanitization (spaces, existing suffixes).
- **Provenance on repeated edit-export-edit cycles:** entries accumulate in
  order; re-exported doc remains a valid input to the full pipeline
  (`tools/play.mjs`).
- **Load-existing-file parity:** all three load paths (example buttons,
  file picker, URL field) — currently only example + picker exercised;
  URL loader exists in the explorer, confirm composer parity.
- **Error panel channel split:** schema / refs / semantics channels shown
  with correct attribution on a doc broken in each channel.

## How to run

`cd explorer && npm test` (vitest); browser pass in the closing note.
