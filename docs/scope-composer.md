# Scope — Composer tool (node-based schema editor)

The write path companion to the read-only explorer (docs/scope-explorer.md):
a node-based visual editor that authors and edits `.muse.json` directly.
Deferred in the vision doc until importer + agent-assisted authoring covered
early needs — that coverage landed (Batch 2), so this tool is now scopable.
Model on the OpenMusic/PWGL lineage per PRIOR_ART_REVIEW.md §2: reuse the
interaction model (node graphs as compositional processes), scope the
ambition (this is a schema editor, not a DAW).

## Decisions (locked)

- **Nodes are schema constructs, not audio.** A node is one of: `motif`,
  `theme`, `rhythm`, `progression`, `section`, `rendition`, `globals`,
  `constraints`. Edges are references (section→material `uses[].ref`,
  section→progression `harmony`, form order). The graph compiles to a
  schema document — the schema remains the source of truth; the graph is a
  projection of it, never the other way around (AGENTS.md schema-first rule).
- **Edit → compile → validate loop.** Every graph edit recompiles to
  `.muse.json` in memory and revalidates against `schema/` +
  `tools/semantics.mjs` + `tools/refs.mjs` — same validation parity rule as
  the explorer (reuse, never reimplement). Invalid states are shown inline
  (red node/edge + error panel), never silently dropped or auto-fixed.
- **Read-only → edit boundary.** Explorer components (validation panel,
  form graph, material browser) are reused as *presentations*; edit chrome
  (node palette, property inspector, edge creation) is composer-only. A
  document open in the composer can be exported/downloaded; there is no
  server-side save (static hosting) — round-trip via file download/upload,
  matching the explorer's load paths.
- **Package layout:** same `explorer/` package, new route/entry
  (`composer/`), reusing the Vite + React + reactflow stack already
  validated. Same Netlify preview; no new deploy surface. Root `npm test`
  unchanged; explorer-side tests stay in the explorer package's own runner.
- **Undo/redo is in scope for MVP** (edit loops without it are unusable);
  multi-user/realtime collaboration is explicitly out.
- **No audio in the composer.** Playback belongs to the player/listener
  surface. Audition = export → player, not embedded.

## Task-list validation (MVP decomposition, per TASK_WORKFLOW.md sizing)

1. **Graph model + round-trip** — `explorer/src/composer/graph.mjs`:
   schema doc → node/edge graph → compiled doc; lossless for all
   `examples/` + `benchmark/corpus/` files (round-trip fixture test).
2. **Composer shell** — route, node palette (construct types above), canvas
   (reactflow), property inspector editing scalar fields (id, bars, energy,
   role from the v0.2 enum, bpm ranges).
3. **Edge/reference editing** — create/edit `uses[].ref` (with transform
   suffix helper), `harmony`, `form.order`; dangling refs flagged live via
   the shared lint.
4. **Material editors** — motif pitch/duration lists (text/grid per
   explorer decision; no piano roll in MVP), progression chord lists,
   rhythm patterns.
5. **Validation + export** — inline error surfacing, download
   `.muse.json`, load existing file; provenance entry appended on save
   (`event: "edit"`, `actor: "composer-tool"`, `ai: false`).

Each is one agent run. Dependencies are linear (1→2→{3,4}→5).

## Consequences for other work

- **Explorer stays untouched** — reuse is import-level (components), not
  behavior changes. The explorer's hard read-only rule stands.
- **No new hosting surface** — the Netlify QA preview deploys whatever lands
  in `explorer/`; composer rides the same build (netlify.toml unchanged).
- **AGENTS.md** "Repository layout" gains `explorer/src/composer/` when the
  MVP lands; this doc is the pointer until then.
