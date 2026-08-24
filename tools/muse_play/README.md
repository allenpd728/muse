# tools/muse_play — P2 reference renderer

Event stream (S1) → audio, soundfont tier (FluidSynth-class with GM
fallback). The renderer-side proof of the S1 contract; L2 lives above.

## CLI

```
python -m muse_play <source> [-o out.wav]
```

source: `.xml`, `.mxl`, `.mid`. Reads through the W1 IR and renders WAV
at 44100 mono.

## Renders

Envelope at pitch frequency: per-part gain, tempo-map conversion,
peak-clip normalization; deterministic on repeat. Sample-tier quality
inherits L2's options (`tools/muse_render`).

## Tests

```
cd tools/muse_play && python -m pytest
```

6 tests: WAV write, notes count, wrapper defaults, determinism, MIDI
source, only-rests failure, empty parts failure.
