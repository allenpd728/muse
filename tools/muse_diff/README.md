# muse_diff — W4 diff tool

IR ↔ IR comparison: recall/precision in tick space, tolerance-configurable.
The ground truth for compression claims and conformance vectors.

## Usage

```bash
python3 tools/muse_diff/cli.py <file_a> <file_b> [--tolerance-ticks N]
python3 tools/muse_diff/cli.py --self-test
```

Exit 0 when identical (recall=precision=1.0), exit 1 otherwise — CI gate
ready. Mismatch classes: missing, extra, onset-drift, velocity-drift.

## API

```python
from muse_diff import diff
report = diff(work_a, work_b, tolerance_ticks=0)
report.recall, report.precision, report.mismatches
```

Greedy deterministic pairing over (part, note) sorted by (onset, pitch,
voice). Rests and unpitched percussion participate like any event.
