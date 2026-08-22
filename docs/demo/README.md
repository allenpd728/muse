# Demo evidence — issue #25 (end-to-end .muse.json → audio)

Two renditions of `examples/full.muse.json`, rendered by
`npm run play -- examples/full.muse.json <rendition-id> --bars 16`:

- `full.r.synthwave.wav` — "Midnight Drive" (synthwave, 100 bpm, analog synth lead), ~77 s
- `full.r.quartet.wav` — "Late Set" (jazz quartet, 88 bpm, piano lead, swing 0.62), ~88 s

22.05 kHz mono 16-bit PCM. Content: the verse section at its repetition
minimum (2×16 bars); `--bars` truncates whole sections only. Same work, two
sanctioned renditions — audibly different tempo, instrumentation, register,
and feel. Regenerate any time; the pipeline is deterministic (offline
expander), so files are byte-stable for a given player/render.mjs version.
