# Demo evidence — issue #25 (end-to-end .muse.json → audio)

Two renditions of `examples/full.muse.json`, rendered by
`npm run play -- examples/full.muse.json <rendition-id> --bars 12`:

- `full.r.synthwave.wav` — "Midnight Drive" (synthwave, 100 bpm, analog synth lead)
- `full.r.quartet.wav` — "Late Set" (jazz quartet, 88 bpm, piano lead, swing 0.62)

22.05 kHz mono 16-bit PCM, ~39–44 s (first 12 bars: verse + chorus).
Same work, two sanctioned renditions — audibly different tempo,
instrumentation, register, and feel. Regenerate any time; the pipeline is
deterministic (offline expander), so files are byte-stable for a given
player/render.mjs version.
