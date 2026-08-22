# Test spec — Explorer #59: .muse.json browser/visualizer MVP

**Source task:** #59 (explorer MVP, per docs/scope-explorer.md)
**Code under test:** `explorer/src/validate.js` (validation parity) and the
pure view-model mappings in `explorer/src/main.jsx` (form graph nodes/edges,
material/rendition card fields).

## Behaviors to verify

- **Validation parity with the repo tooling** — the one place the explorer
  could silently drift from `npm run validate` / `tools/semantics.mjs`:
  - For every `examples/*.muse.json`: `validateDocument(doc)` returns zero
    issues.
  - For every `examples/invalid/*.muse.json`: `validateDocument` returns at
    least one issue whose `channel` equals the sidecar's pinned `channel`
    and whose message contains each `messages[]` entry (same assertions the
    harness's mustReject makes, run against the browser code path).
  - Pin that the bundled schemas are the repo's actual files (the Vite
    imports resolve to `schema/`, not a copy).
- **`tools/refs.mjs` extraction is behavior-preserving** — already covered
  transitively (harness + tests import through `tools/test.mjs` re-export,
  39/39 green); no new assertions needed unless the re-export is removed.
- **View-model mapping** (if `main.jsx` grows logic worth pinning; currently
  presentational): form graph nodes follow `form.order`, ghost sections
  (order entries with no matching section) render distinctly, repetition
  bounds appear on nodes.
- **Explorer has no test runner yet** — add a minimal one (e.g. vitest for
  `validate.js` parity checks against the examples, which runs in node).
  UI smoke (React rendering) is out of scope unless the owner wants it.

## How to run

`cd explorer && npm test` once the runner exists; the parity check should
also be runnable from the repo root so CI picks it up when Actions is back.
