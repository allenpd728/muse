# Test spec — Composer MVP 4 #82: material editors

**Source task:** #82 (motif pitch/duration lists, progression chords, rhythm
patterns — text/grid, no piano roll)
**Code under test:** `explorer/src/composer/main.jsx` (parseList, ListEditor).

Coverage landed with the task: `explorer/src/composer/material.test.mjs` —
9 vitest checks (parseList per kind ×5, edits through compile ×4) plus a
browser pass (motif inspector shows list editors; invalid token held
locally with error styling, last-good value preserved). This spec is for
what remains.

## Behaviors to verify

- **UI-level edit round-trip:** typed input → recompiled doc assertion via
  a DOM/component test (current tests drive parseList/compile directly).
- **List/scalar interplay:** editing pitches then switching nodes and back
  (the useEffect resync path) — no stale text, no lost edit.
- **Grid mode:** scope says "text/grid" — only text landed; if a grid
  editor is added (duration cells, chord slots), pin per-cell validation
  and add/remove-row behavior.
- **Motif kind transitions:** a motif with kind rhythm edited to carry
  pitches (or pitch motif cleared to empty) — kind field editing itself is
  MVP 5+ scope; pin behavior when it lands.
- **Empty-list legality:** clearing a motif's pitches entirely — schema
  allows empty arrays; must_contain recall degrades to unfound (benchmark
  metric) — pin that the composer surfaces this as info, not error.

## How to run

`cd explorer && npm test` (vitest); browser pass in the closing note.
