# Test spec — Composer MVP 2 #80: composer shell

**Source task:** #80 (composer shell: route, palette, canvas, inspector)
**Code under test:** `explorer/src/composer/main.jsx` (+ `composer.html`,
vite multi-entry).

Coverage landed with the task: `explorer/src/composer/composer.test.mjs` —
5 vitest checks (roles enum ⇔ schema pin, palette coverage, scalar
edit → compile → validate loop ×3) — plus a manual browser pass: shell
renders, full example loads into the canvas with typed edges, node select
opens the inspector, role dropdown shows the v0.2 enum. This spec is for
what remains.

## Behaviors to verify

- **Inspector round-trip through the UI:** a scripted browser test (or
  component test with a DOM renderer) that loads the full example, edits
  `energy`, and asserts the recompiled doc — the current tests drive
  graph.mjs directly, not the React layer.
- **Palette add-node behavior:** new node appears with a fresh key;
  globals/constraints singleton guard blocks a second add; section nodes
  default `role: "custom"` (schema-valid).
- **Undo/redo** (scope-locked for MVP, not yet implemented): when it
  lands, pin edit → undo → redo ⇒ doc equality at each step.
- **Explorer/build regression:** `vite build` multi-entry must keep both
  `index.html` and `composer.html` outputs; explorer routes (`/`) must not
  404 on the Netlify deploy (SPA fallback is not configured — static
  multi-page only).
- **Import-safety:** `main.jsx` must stay import-safe in node (mount
  guarded) — pinned implicitly by composer.test.mjs importing it; keep.

## How to run

`cd explorer && npm test` (vitest); build check `npm run build`; browser
pass documented in the closing note.
