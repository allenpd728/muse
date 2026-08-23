# muse_viz — W5 visualizer

IR → piano-roll plots. Founder review aid. matplotlib; 52-part-safe via
part selection (`--first N` / `--parts id1,id2`) and per-note alpha.
Design: [docs/design/w5-visualizer.md](../../docs/design/w5-visualizer.md).

## Usage

```bash
python3 tools/muse_viz/cli.py <file> [--parts P1,P2] [--first N] [--out x.png]
```

## API

```python
from muse_viz import render, PianoRollConfig

render(work, PianoRollConfig(parts=["P1", "P2"], out="chorale.png",
                             title="Bach BWV227.1", alpha=0.6))
```

Each part renders as a lane; notes as bars positioned by onset and duration.
Rests (`pitch=None`) and unpitched percussion map to sentinel lanes
(`-1` / `-2`) — no crash, distinct positions. `render()` returns a
`RenderResult(path, parts_rendered, events)`.

## Architecture

matplotlib Agg backend (no runtime service deps). One subplot per part,
sharex=False (parts may have different ranges). Color via `tab20` cycling
by part-id hash. Zero-duration notes clamped to width=1.

## Tests

11 tests: chorale/Byrd render, Beethoven 9 subset, None-pitch robustness,
zero-duration clamp, part selection. Test spec:
[tests/open_20260823-192000_w5-visualizer.md](../../tests/open_20260823-192000_w5-visualizer.md).

Dependencies: `pip install matplotlib`.
