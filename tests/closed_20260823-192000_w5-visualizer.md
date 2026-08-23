# Test spec — W5 visualizer — CLOSED

**Task:** #127 (W5 — Visualizer)
**Written:** 2026-08-23

**Resolution (Tests: #134, 2026-08-23):** landed as
`tools/muse_viz/test_muse_viz.py` — 11 tests, ~33s (B9 parse dominates).
All three spec sections covered (rendering on Bach/Byrd/B9-subset,
robustness for rests/unpitched/zero-duration/subsets, output contract with
PNG magic-byte checks). Fixes landed with the tests: unpitched percussion
now maps to sentinel −2 (the code looked for an `is_unpitched` attribute
from the superseded IR; the landed IR uses the `unpitched` notation flag),
and `render()` returns a `RenderResult` so the output contract is testable
without image introspection.

## What to verify

1. **Rendering**
   - Bach chorale (4 parts) renders legibly
   - Byrd Kyrie (3 parts, MIDI path) renders legibly
   - Beethoven 9 subset renders without error (52-part-safe: `--first N`
     or `--parts` CLI selection works)

2. **Robustness**
   - None-pitch rests (sibling IR) map to a low sentinel, no crash
   - Unpitched percussion maps distinctly (sentinel -2 vs -1)
   - Zero-duration notes render (clamped width)
   - Part subset selection (`--parts id1,id2`) renders only those rows

3. **Output**
   - PNG written; title includes part count + event count

## How to run

```bash
python3 tools/muse_viz/cli.py corpus/bach/bwv227.1.mxl --out chorale.png
python3 tools/muse_viz/cli.py corpus/byrd/1-Kyrie.mid --out byrd.png
python3 tools/muse_viz/cli.py corpus/beethoven/beethoven-sym9.xml --first 8
```
