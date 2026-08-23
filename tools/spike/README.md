# tools/spike — spike-grade pipeline scripts

These scripts produced the committed artifacts in `docs/spike/`. They are
**spike-grade**: hand-rolled, hardcoded paths, no tests. They exist so the
spike is reproducible from a fresh sandbox — they are NOT the final
architecture (the W-series tools replace them properly).

## Scripts

| Script | What it does | Spike step |
|---|---|---|
| `extract_phrase.py` | MusicXML (.mxl) → phrase IR JSON (first N measures, SATB) | score extraction |
| `build_midi.py` | phrase IR + mockup JSON → MIDI (mechanical + interpreted) | Tier 1 (GM) render prep |
| `render_sso.py` | phrase IR + mockup JSON → WAV via SSO SFZ string samples | Tier 2 (samples) render |

## Environment setup (fresh sandbox)

```bash
sudo apt-get install -y unzip fluidsynth fluid-soundfont-gm
pip install numpy soundfile mido

# Sonatina Symphonic Orchestra (CC-licensed samples, ~1.4GB)
curl -sL https://github.com/peastman/sso/archive/refs/heads/master.zip -o /tmp/sso.zip
unzip -q /tmp/sso.zip -d /tmp/sso
```

Scripts expect: SSO at `/tmp/sso/sso-master/`, phrase IR at
`/tmp/chorale-phrase.json`, mockups at `/tmp/mockup-v*.json`. Adjust paths at
the bottom of each script.

## Provenance

- SSO: https://github.com/peastman/sso — CC Sampling Plus license
- VSCO 2 CE: https://github.com/sgossner/VSCO-2-CE — CC0; downloaded but
  unused (ships without SFZ mappings in that repo state)
- FluidR3 GM: system package `fluid-soundfont-gm` (Tier 1 renders)
