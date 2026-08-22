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

---

## Closed — 2026-08-22 (issue #96)

Coverage landed (appended to `explorer/src/composer/export.test.mjs`,
now 7 checks):

- **Export filename pinned:** `exportFilename` extracted — spaces
  collapse, existing `.json`/`.muse.json` suffixes normalize (case-
  insensitive), undefined → `untitled.muse.json`.
- **Pipeline validity:** an exported doc (provenance appended) plays
  end-to-end through `tools/play.mjs` — WAV with a RIFF header produced
  (vitest drives the real CLI with a 30s budget).

Deferred (still open, with triggers):

- **Download round-trip through the browser** — scripted-browser
  territory (the Blob/download helper is untestable in vitest; the
  DOM-renderer decision from #93–#95 covers this too).
- **Load-path parity (URL field)** — composer currently has example
  buttons + file picker; the explorer's URL loader is a separate
  component — parity is a small port, flag if wanted.
- **Error panel channel split** — channels render with attribution today
  (the panel labels each issue `[schema]`/`[refs]`/`[semantics]`); a
  broken-in-each-channel visual pass is a browser check, not vitest.

Run: `cd explorer && npm test`.
