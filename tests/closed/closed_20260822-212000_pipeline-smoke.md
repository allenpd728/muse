# Test spec: pipeline smoke residual coverage (follow-up to #105)

**Source task:** #105 (CLI end-to-end smoke + listener end-to-end)
**Code under test:** `tests/play-smoke.test.mjs` (CLI path),
`explorer/src/listen/listen-smoke.test.js` (listener path). This spec covers
what remains.

## Behaviors to verify

- **Rendered audio sanity beyond non-silence:** peak amplitude and RMS floors
  per rendition — the offline expander's density/swing params must produce
  audibly distinct buffers, not just different bytes (the #25 test asserts
  byte difference; pin the *level* difference too).
- **Tempo-map interpolation in rendered output:** a doc with a mid-piece tempo
  change renders at two audible rates — pin by measuring onset spacing before
  and after the change in the rendered buffer.
- **Listener smoke across both renditions:** currently one rendition; add the
  quartet path so both directions of the A/B switch are covered at the seam.
- **Failure channel:** `tools/play.mjs` on a schema-invalid doc exits 1 with a
  readable error (no partial WAV) — the CLI's own validate-before-write guard
  exercised through the play path.

## How to run

Extend `tests/play-smoke.test.mjs` / `explorer/src/listen/listen-smoke.test.js`;
`npm test` and `cd explorer && npm test` pick them up automatically.

## Resolution

Coverage landed via issue #109 (sibling agent, commit bbfb5f5): amplitude/RMS
floors per rendition, tempo-map interpolation in rendered output, listener
smoke across both renditions, and the play CLI failure channel. Spec file
closed post-hoc — the work predates this rename.
