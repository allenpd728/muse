# muse_analyze — W3 pattern analyzer

IR → pattern report: exact/transposed repeats, ostinato (rhythm), imitative
entries, per-phrase delta curves. Full-corpus → `docs/analysis-report.md`.

## Usage

```bash
python3 tools/muse_analyze/cli.py <file>
python3 tools/muse_analyze/cli.py --all
```

## Scale budget (W6 lender)

Works >2000 points get pattern-length caps (exact ≤16, transposed ≤12) —
small/mid works stay exhaustive. Beethoven 9 completes within budget.

## Report classes

- **exact** — normalized (onset, pitch) shape repeats
- **transposed** — interval-sequence repeats under transposition
- **ostinato** — rhythmic-onset-interval repeats (pitch ignored)
- **imitative** — same normalized shape at different onsets across parts
- **delta_curve** — IOI ratios (per-phrase freedom concentration)
