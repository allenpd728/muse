# tools/muse_render — L2 performance renderer

Mockup → audio via sfizz+SFZ samples (SSO/VPO tier, when present) and a
FluidSynth-fallback sine-envelope path (satisfies the spike's "worth
listening to" bar on the small test set while the sfizz toolchain isn't
landed yet).

## CLI

```
python -m muse_render <mockup.json> [-o out.wav]
```

## Architecture

Per-note attack/decay/sustain/release envelope at the pitch frequency,
per-part gain, tempo-map time conversion (the SPIKE's render_sso.py scheme
generalized over the mockup model). Normalized peak-clip protection.

## API

```python
from muse_render import render_to_file
meta = render_to_file(mockup, "out.wav")
```

## Tests

```
cd tools/muse_render && python -m pytest
```

6 tests: WAV write, notes count, tempo-map duration driving, determinism,
clip normalization, loud failure on empty mockup.
