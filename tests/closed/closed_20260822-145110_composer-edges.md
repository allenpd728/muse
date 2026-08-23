# Test spec — Composer MVP 3 #81: edge/reference editing

**Source task:** #81 (uses[].ref + transform helper, harmony, form.order,
live dangling-ref flags)
**Code under test:** `explorer/src/composer/main.jsx` edge operations;
`explorer/src/composer/graph.mjs` compile edge-wins semantics.

Coverage landed with the task: `explorer/src/composer/edges.test.mjs` — 12
vitest checks (edge type inference ×6, ref helper ×2, compile-level
operations ×5) plus a browser pass (inspector uses/harmony/form-order UI
on the full example). This spec is for what remains.

## Behaviors to verify

- **onConnect through the real canvas:** reactflow drag-connect creates a
  typed edge — component/DOM-level test or scripted browser; current tests
  drive the pure operations, not the React event path.
- **Order-edge insert vs append:** dragging a new section→section link
  appends an order edge; inserting mid-sequence (A→C becomes A→B→C) is a
  UX decision deferred — pin when chosen.
- **Uses edge dedup:** connecting the same section→material pair twice —
  currently allowed (mirrors schema, which allows duplicate uses entries);
  decide and pin.
- **Edge deletion on canvas (reactflow onEdgesDelete):** only inspector ✕
  works today; keyboard/canvas deletion unhandled.
- **compile() edge-wins semantics:** uses/harmony delete clears stale
  projected fields (fixed this task: `delete s.uses/s.harmony` when no
  edges) — round-trip suite in graph.test.mjs should gain a removal case
  to pin the behavior (currently covered in edges.test.mjs only).

## How to run

`cd explorer && npm test` (vitest); browser pass in the closing note.

---

## Closed — 2026-08-22 (issue #94)

Coverage landed:

- **compile() edge-wins pin:** `graph.test.mjs` gains the removal case —
  deleting all uses/harmony edges clears the stale projected fields
  (uses/harmony undefined on compile).
- **Uses dedup decision (pinned):** duplicate uses edges stay allowed —
  they mirror the schema (uses[] is an array; repeated material in a
  section is legal). A UX-level dedup, if ever wanted, lands deliberately.
  Pinned in `edges.test.mjs`.

Deferred (still open, with triggers):

- **onConnect through the real canvas** — same DOM-renderer dependency as
  the #93 UI-level item (jsdom/happy-dom decision for the human).
- **Order-edge insert vs append** — UX decision deferred; pin when chosen.
- **Canvas edge deletion (onEdgesDelete)** — unhandled today; pin when
  wired.

Run: `cd explorer && npm test`.
