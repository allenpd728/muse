# muse_analyze — W3 pattern analyzer

IR → pattern report: exact/transposed repeats, ostinato (rhythm), imitative
entries, per-phrase delta curves. Full-corpus → `docs/analysis-report.md`.
Design: [docs/design/w3-pattern-analyzer.md](../../docs/design/w3-pattern-analyzer.md).

## Usage

```bash
python3 tools/muse_analyze/cli.py <file>      # per-work summary
python3 tools/muse_analyze/cli.py --all       # full corpus → docs/analysis-report.md
```

## API

```python
from muse_analyze import analyze, PatternReport

report = analyze(work, name_hint="bach")
report.exact         # {pattern_tuple: [onsets]} — normalized shape repeats
report.transposed    # {pattern_tuple: [onsets]} — interval-sequence repeats
report.ostinato      # {interval_seq: count} — rhythm-only repeats
report.imitative     # {pattern: [(part, onset)]} — cross-part shares
report.delta_curve   # [(onset, ioi_ratio)] — per-phrase freedom concentration
report.summary()     # human-readable counts per class
```

## Architecture

Point-set normalized matching: `(onset, pitch)` events, normalized to onset=0
(exact), pitch-pp=0 (transposed), pitch-negated (mirror), reversed
(retrograde). Ostinato runs on onset intervals only (pitch ignored).
Imitative detection checks normalized shapes across parts.

## Scale budget (W6 lender)

Works >2000 points get pattern-length caps (exact ≤16, transposed ≤12);
small/mid works stay exhaustive. Beethoven 9 completes within budget
(252k distinct exact patterns — the compressibility evidence).

## Tests

17 fast + 15 slow (corpus pins + Beethoven 9 budget): pattern-class presence,
scale-budget ladder, delta curve, CLI per-work + --all structs.

**Slow gate:** Beethoven 9 analysis is ~30s alone (239k notes). Fast runs skip
the slow set by default:

```bash
MUSE_SKIP_SLOW=1 python3 -m pytest tools/muse_analyze/   # fast (17 tests)
python3 -m pytest tools/muse_analyze/                    # full (32, ~30s)
```

Corpus pins and B9 budget are marked `@slow`; CI runs full, local dev gates fast.

Test spec:
[tests/open_20260823-204500_w3-pattern-analyzer.md](../../tests/open_20260823-204500_w3-pattern-analyzer.md).
