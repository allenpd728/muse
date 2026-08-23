# muse_diff — W4 diff tool

IR ↔ IR comparison: recall/precision in tick space, tolerance-configurable.
The ground truth for compression claims and conformance vectors. Design:
[docs/design/w4-diff-tool.md](../../docs/design/w4-diff-tool.md).

## Usage

```bash
python3 tools/muse_diff/cli.py <file_a> <file_b> [--tolerance-ticks N]
python3 tools/muse_diff/cli.py --self-test
```

Exit 0 when identical (recall=precision=1.0), exit 1 otherwise — CI gate
ready.

## API

```python
from muse_diff import diff, DiffReport, Mismatch

report = diff(work_a, work_b, tolerance_ticks=0)
report.recall        # matched / total_a
report.precision     # matched / total_b
report.mismatches    # [Mismatch(kind, pitch, onset_a, onset_b, part)]
report.ok()          # recall == 1.0 and precision == 1.0
```

## Architecture

Greedy deterministic pairing: both walks advance monotonically over
`(part_id, note)` sorted by `(onset, raw_pitch, voice)`. Raw pitch maps
`None` → -1 (rests/unpitched participate like any event). Mismatch classes:
`missing`, `extra`, `onset-drift`, `velocity-drift`.

Robust to either IR layout (superseded `tools/muse_ir` and current
`tools/ir`).

## Tests

15 tests: self-diff=1.0, deletion → recall, insertion → precision, drift
classified within tolerance. Test spec:
[tests/open_20260823-191500_w4-diff-tool.md](../../tests/open_20260823-191500_w4-diff-tool.md).
