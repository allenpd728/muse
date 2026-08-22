# Scope — Player V2: audio-model plugins

Design gate for the pro tier from `docs/scope-batch3.md`: neural/audio-model
renderers that plug into the Player through the spec-sanctioned
`extensions.<namespace>` slot. V1 stays the conformance reference — plugins
are swappable timbral engines, never landlords (vision doc: "Models compete;
the format collects the rent"). Design doc only; no code.

## Decisions (locked)

- **The renderer contract from scope-batch3 is the plugin boundary, unchanged:**

  ```js
  const renderer = {
    id: "renderer.my-model",            // extensions.<namespace> name
    capabilities: () => ({ streaming: false, controllers: ["pitch_bend"] }),
    render: async (perfDoc, { sampleRate, window }) => Float32Array[], // per channel
  };
  ```

  The only extension to the Batch 3 contract is the optional `window`
  parameter (`{ startBeat, endBeat }`) — see rendering modes below. A plugin
  that ignores `window` renders the whole document; one that rejects an
  unsupported window throws, and the caller degrades (see failure behavior).
  Plugins are stateless per render and ship their own license record.
- **Rendering modes — settled as full-mix or per-part stems, never per-note.**
  A plugin declares its mode in `capabilities().mode`:
  - `"full-mix"` — consumes the entire performance document (or a window of
    it) and returns the mixed audio. Simplest model contract; the plugin sees
    everything and owes one buffer.
  - `"stem"` — consumes the document plus a `part` selector and returns one
    part's audio; the player mixes stems using the document's `mix`
    directives (gain/pan/reverb_send). Enables per-instrument model
    specialization (the furthest-along research area) and lets a rendition
    mix tiers: neural strings, V1 drums.
  - *Per-note rendering is rejected:* note-granular model calls lose all
    temporal context (articulation across notes, phrase-level timbre), and
    the call count makes it impractical. A model that wants note-level
    conditioning gets it via `window` in stem or full-mix mode.
- **Backend selection:** `renditions[].extensions.<renderer-id>` selects and
  configures the plugin for that rendition (that is what the extensions
  namespace is for — engine-specific knobs, per AGENTS.md). The value is a
  plain object owned by the plugin's namespace: e.g.
  `"extensions": { "renderer.my-model": { "checkpoint": "v2.1", "cfg": 3.5 } }`.
  Unknown/absent namespaces → the player renders with V1 (existing
  conformance behavior: engines ignore unknown namespaces, never fail).
  Selection is per-rendition, so two renditions of the same schema can use
  different backends — that comparison *is* the benchmark surface.
- **Failure/degradation: always degrade to V1, loudly.** Any plugin error —
  load failure, unsupported window/controller, render exception, output that
  fails sanity checks (wrong channel count, NaNs, silence) — falls back to
  the V1 renderer for the affected scope (whole document or the failed
  stems). The fallback is recorded: the render result carries
  `degraded: [{ renderer, scope, reason }]` so callers and the conformance
  harness can see it happened. A silent fallback is a bug; audio that
  quietly sounds worse is worse than no audio.
- **V1 is the conformance reference.** Conformance is measured against the
  schema's constraints and the performance document, not against any
  renderer's output. Plugin renders are subject to the same motif-recall /
  structure-fidelity harness as V1 (Batch: benchmark #72); a plugin that
  fails conformance on the canonical corpus is demoted in listings, not
  accommodated. New capabilities (controllers a plugin supports) flow through
  `capabilities()`; the player strips unsupported per-note controller data
  before calling `render`.
- **Provenance and licensing:** plugin-rendered output is AI-generated
  audio, and the platform's rights posture applies. A render that used a
  plugin must record it in the *originating schema document's*
  `metadata.provenance` on export/distribution: `event: "render"`, `actor`
  = renderer id, `ai: true`, `notes` = plugin version/checkpoint. Plugins
  must declare training-data/license posture in their license record;
  named-artist or voice-likeness targeting is prohibited exactly as in
  rendition `style.references` (§2.6 hard rule), and a plugin whose declared
  purpose violates it is not loadable.

## Consequences for other work

- **#72 (conformance harness)** — the harness gains a second subject: plugin
  renders. Same metrics, plus `degraded` must be empty for a conformance pass.
- **Performance document** — no changes required; `window` operates on the
  beat clock that already exists. `controllers` payloads a plugin declares
  unsupported are stripped by the player, so the document format stays
  superset.
- **Explorer** — rendition cards may later surface which backend a rendition
  selects (the extensions namespace is already visible in the document tree).
  No explorer work now.
