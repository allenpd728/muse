# Test spec — Listener MVP 4 #100: WAV download

**Source task:** #100 (renderWav client-side; download active rendition
render)
**Code under test:** `player/render-core.mjs` (encodeWav),
`explorer/src/listen/ListenTab.jsx` (downloadWav).

Coverage landed with the task: `explorer/src/listen/wav.test.js` — 5
vitest checks (Uint8Array/no-Buffer, RIFF header + sizes, stereo/16-bit/
rate, PCM body matches rendered channels, byte-for-byte equality with the
node renderWav path) plus a browser pass (⬇ wav button in the transport).
This spec is for what remains.

## Behaviors to verify

- **Download filename:** `<title>.<rendition-id>.wav` — pin sanitization
  (spaces collapse; missing title → "muse").
- **Download integrity in a real browser:** the Blob round-trips — a
  scripted-browser test downloading and re-reading the file (the Blob
  helper is untestable in vitest; the DOM-renderer decision from the
  composer lineage covers this).
- **Download after A/B switch:** the perf cache tracks the ACTIVE
  rendition — switch A→B then download: the WAV is B's render, not A's
  (the perfs cache is keyed by rendition id; pin no stale-cache bug).
- **Provenance continuity:** the perf doc's metadata.interpreter (stamped
  at expansion) travels with the download conceptually — the WAV has no
  metadata channel; if a listener wants provenance, the perf JSON should
  be downloadable too (UX decision, flag).
- **Long renders:** full-length pieces (~4 min stereo 44.1k = ~40MB
  Uint8Array) — memory behavior on download; pin a size guard or
  streaming decision if this becomes a problem.

## How to run

`cd explorer && npm test` (vitest); browser pass in the closing note.
