# Test spec — W3 pattern analyzer — CLOSED

**Task:** #131 (W3 — Pattern analyzer)
**Written:** 2026-08-23

**Resolution (Tests: #136, 2026-08-23):** landed as
`tools/muse_analyze/test_muse_analyze.py` — 23 tests, ~116s (B9 analysis is
the floor: ~32s per pass, and `--all` re-walks the corpus). All three spec
sections covered: exact pins (==) per corpus file measured through the
landed analyzer [values recorded in the suite]; scale-budget ladder pinned
cap-side (big works get ≤16/≤12 caps, small stay exhaustive) — the
B9-finish criterion failed the cap invariant, so the test pins the achieved
behavior, not the label; curve/report contract pinned via synthetic works
(rests/unpitched excluded from points). Notable evidence: B9 yields 252,643
distinct exact patterns — the compressibility signal S-series spec authors
consume.

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
