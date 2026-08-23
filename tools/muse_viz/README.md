# muse_viz — W5 visualizer

IR → piano-roll plots. Founder review aid. matplotlib; 52-part-safe via
part selection (`--first N` / `--parts id1,id2`) and per-note alpha.

## Usage

```bash
python3 tools/muse_viz/cli.py <file> [--parts P1,P2] [--first N] [--out x.png]
```

Renders each part as a lane; notes as bars positioned by onset and pitch.
Rests/unpitched map to sentinel lanes (low negative pitches).

Dependencies: `pip install matplotlib` (Agg backend, no service deps).
