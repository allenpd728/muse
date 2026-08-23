# Test spec — W3 pattern analyzer

**Task:** #131 (W3 — Pattern analyzer)
**Written:** 2026-08-23

## What to verify

1. **Pattern classes**
   - Exact repeats found in Bach chorale (known theme structure)
   - Transposed repeats found (sequence detection)
   - Ostinato (rhythm-only intervals) counted
   - Per-phrase delta curve (IOI ratios) non-empty on any work

2. **Scale budget** (W6 ladder)
   - Works with >2000 points: pattern lengths capped (exact ≤16, transposed ≤12)
   - Small/mid works: exhaustive within limits
   - Beethoven 9 completes within budget (the ratchet's top rung)

3. **CLI**
   - Per-work: reports counts per class
   - `--all`: full corpus → docs/analysis-report.md

## How to run

```bash
python3 tools/muse_analyze/cli.py <file>
python3 tools/muse_analyze/cli.py --all
```

The report counts are evidence for S-series constructs (a construct without
corpus evidence doesn't ship — locked).
