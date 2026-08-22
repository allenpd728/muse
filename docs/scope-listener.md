# Scope — Listener prototype (schema → rendition → hear it)

The last unbuilt pipeline step (docs/pipeline.md step 7) and the vision doc's
proof point: *same file + different rendition = a different performance.*
This is the listener-facing surface — open a `.muse.json`, pick a rendition,
hear the piece.

## Decisions (locked)

- **Placement: a "Listen" tab in the existing `explorer/` package**, not a
  separate app. Load paths (file/URL/examples), rendition cards, and
  validation are already there; the vision's listener UX is exactly
  "open → pick rendition → hear," which is one view over what exists. A
  separate listener app can split off later if it grows a player chrome of
  its own — for the prototype, a new package is dead weight.
- **Playback path: in-browser WebAudio synthesis from the performance
  document** — not pre-rendered WAV artifacts. Rationale:
  - `player/render.mjs` is already pure Float32Array synthesis with no node
    imports — it ports to WebAudio as-is (write channels into an
    `AudioBuffer`, play via `AudioBufferSourceNode`). No assets, no ffmpeg,
    no committed WAVs rotting in the repo.
  - The seam to pre-rendered artifacts is the performance document itself:
    a later "download WAV" affordance runs the same `renderWav` path
    (16-bit PCM encode already exists) client-side. Nothing about the MVP
    forecloses serving pre-rendered audio later for slow LLM interpretations.
- **Interpreter: offline heuristic only in MVP.** `interpreter/offline.mjs`
  is deterministic, dependency-free (its only imports are the IR pitch
  helpers, browser-safe), and produces audible differences between
  renditions by construction. The LLM path (`expand.mjs`) is
  bring-your-own-key per the vision doc, but **no LLM calls run client-side
  in the prototype** — keys in a browser are a footgun and CORS/egress make
  it fragile. The seam: a later "interpret with model…" option can POST to a
  thin proxy; the listener's interpreter interface (`expandOffline(doc,
  rendition)` → performance doc) already matches `expand`'s shape.
- **The demo moment: rendition A/B switch with continuous transport.**
  Both renditions are expanded and rendered to buffers up front; switching
  renditions crossfades at the current playback position (same schema →
  same structure → positions are comparable by construction). This is the
  product argument made audible, so it is in MVP, not polish.
- **Read-only posture holds.** The listener never edits the document; it
  reuses the explorer's validation panel state (a document that fails
  validation shows the errors and does not render playback controls).

## MVP decomposition (per TASK_WORKFLOW.md sizing — one run each)

1. **Webaudio playback core** — port `player/render.mjs` output into an
   AudioContext (buffer build, play/pause/seek, stop). Module: pure
   `explorer/src/listen/player.js` wrapping the existing render function;
   fixture test on buffer length/channel count (node can exercise the math
   without an AudioContext via a thin stub).
2. **Listen tab** — rendition cards gain a play affordance; offline
   expansion on selection; transport bar (play/pause, position, section
   marker from the form graph). Reuse rendition cards verbatim.
3. **A/B rendition switch** — second rendition pre-rendered; switch button
   crossfades at current position; elapsed/section continuity preserved.
4. **WAV download** — `renderWav` exposed client-side; downloads the active
   rendition's render (provenance already stamped in the performance doc).

Dependencies linear: 1 → 2 → {3, 4}.

## Consequences for other work

- **#91 (offline interpreter gaps)** is the blocker on imported content
  sounding like anything — the listener's demo content is
  `examples/full.muse.json` until corpus imports realize notes.
- **Explorer** gains the tab and `player.js`; the read-only rule stands
  (transport state is not document state).
- **Batch 3 player** — `render.mjs`/`renderWav` are reused, not ported;
  any bug fixes land there, not in a fork.
