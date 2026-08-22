# Scope — Explorer (.muse.json browser/visualizer)

First frontend surface: a static web app to browse, visualize, and validate
Muse schema documents. No dependency on Batch 3 — it works on the schema
alone and is immediately useful for debugging importer output. Per
PRIOR_ART_REVIEW.md §7, inspectability is the differentiator no closed
platform exposes; the explorer is where that property becomes visible.

## Decisions (locked)

- **Views (five, build order as listed):**
  1. **Validation panel** — schema errors (ajv against `schema/`), cross-ref
     lint (`danglingRefs`), semantics lint (`checkSemantics`). First because
     the immediate use is debugging importer output: a document that fails
     must show *why* before anything renders.
  2. **Document tree** — collapsible JSON tree of the whole document
     (JSON Crack / Stoplight class). The fallback view for documents too
     broken to visualize structurally.
  3. **Form graph** — sections as nodes, `form.order` as the navigable
     sequence, `repetition` bounds shown on the node. This is the view no
     generic JSON tool provides and the one that makes the spec legible.
  4. **Material browser** — motifs/themes/rhythms/progressions as structured
     lists; transform-suffixed refs (`motif.a#seq(+2)`) displayed with the
     transform readable, linked to the base material. Text/grid rendering of
     pitches and durations only; piano-roll-style graphics are explicitly
     later.
  5. **Rendition cards** — one card per preset: name, style (genre/era/
     references), params, author. Read-only presentation of what a listener
     would pick among.
- **Read-only, hard boundary.** The explorer never mutates the document.
  Test for drift: if a UI element would produce a modified `.muse.json`, it
  belongs to the composer tool (deferred per `docs/vision.md` component 6),
  not here. No inline editors, no "fix this error" buttons, no save/export
  of altered documents. Copy-to-clipboard is allowed (no mutation).
- **Stack:** static site, no backend. Vite + React (plain JSX — no
  TypeScript; the repo has none and one app doesn't justify a compiler).
  React Flow for the form graph (per prior-art §2's pointer at the React
  Flow / LiteGraph class; React Flow is DOM-native React and MIT, LiteGraph
  is canvas-based audio-patch tooling). Loads a document from **file picker
  or URL** (URL fetch is CORS-dependent; failure surfaces as a load error,
  not a crash).
- **Validation is reused, not reimplemented:**
  - `schema/*.schema.json` are bundled statically (Vite JSON imports) and
    registered with ajv (draft 2020-12, browser-compatible) — the same files
    `npm run validate` uses, not copies.
  - `tools/semantics.mjs` imports cleanly in the browser already (pure ESM,
    no node imports).
  - `danglingRefs` currently lives in `tools/test.mjs` beside node-only
    imports (`fs`, `child_process`), so it cannot be bundled. **Extract**
    `danglingRefs` + `baseRef` into a pure `tools/refs.mjs`; `tools/test.mjs`
    re-exports from there so existing harness and test imports are
    unchanged. This extraction is part of the MVP task, not a separate
    refactor.
  - `tools/validate.mjs` is a node CLI and stays that way; the explorer
    composes ajv directly. The *logic* reused is the schema set plus the two
    lint modules — the CLI wrapper itself is node-specific by design.
- **Package layout:** `explorer/` is its own npm package (own
  `package.json`, Vite project). Keeps the root `npm ci` lean for the
  schema/importer harness and lets Netlify build the explorer in isolation.
  Root `npm test` is unchanged and does not cover the explorer (a static
  app's test story, if wanted, is a separate decision).
- **Hosting:** Netlify branch preview from this repo — `explorer/` in-repo,
  `netlify.toml` with `base = "explorer"`, `build = "npm run build"`,
  `publish = "dist"`. Branch deploy on `dev` (previews track the working
  branch; promotion to a `main`-based deploy waits for a milestone merge,
  same as everything else). No custom backend, no serverless functions.

## Task-list validation

- **#59 (Explorer MVP)** — the DoD maps onto these decisions without
  re-scoping: renders `examples/minimal.muse.json` and `full.muse.json`
  (views 1–5), validation parity with `npm run validate` /
  `tools/semantics.mjs` (reuse decisions above — including the `refs.mjs`
  extraction), static build deployable to a Netlify branch preview (hosting
  decision). The example documents double as the explorer's dev fixtures.

## Consequences for other work

- **Importer feedback loop:** the explorer is the inspection surface for
  `extensions.importer.inferred` — Batch 2's marked inferences should be
  visible in the validation panel or document tree without special-casing
  (they are ordinary document content). No importer changes required.
- **Batch 3:** the explorer deliberately stops at the schema. Playback,
  performance documents, and rendition *switching with audio* belong to the
  listener front end, which reuses the rendition-card and validation-panel
  concepts but not this app.
