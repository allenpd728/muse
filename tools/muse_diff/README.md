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

Two paths, because the chain's own call is `tolerance_ticks=0` (exact
reconstruction) and that case need not search:

| Path | Complexity | Pairing |
|---|---|---|
| `tolerance == 0` | **O(n_a + n_b)** | a bucket on `(pitch, onset)`; an exact match is fully determined by that key |
| `tolerance > 0` | greedy nearest-onset search | unchanged |

Both walks are sorted by `(onset, raw_pitch, voice)`. Raw pitch maps
`None` → -1 (rests/unpitched participate like any event). Mismatch classes:
`missing`, `extra`, `onset-drift`, `velocity-drift`. The **match key is pitch
and onset only** — `part` is reported in mismatches but never matched on,
which matches the tolerance>0 path. Among equal keys the lowest `b` index
wins, so a FIFO bucket reproduces the old pairing exactly (pinned by
`test_duplicate_keys_pair_in_b_index_order`).

Robust to either IR layout (superseded `tools/muse_ir` and current
`tools/ir`).

### Why the exact path matters (issue #317)

The tolerance-0 path scanned every unmatched `b` note for every `a` note,
plus a per-note `list(unmatched_b)` allocation — O(n_a × n_b). Beethoven 9,
**the v1.0 conformance target** at 239,459 notes, exceeded 15 minutes; that
is why `tools/muse_chain` SKIPped `verify(W4)` for it, leaving "the score
reconstructs losslessly" unproven on the one work the format is built for.

With the keyed path:

```
B9 self-diff: 0.99s   recall=1.0 precision=1.0 matched=239459
```

A scaling test pins it: doubling n must not quadruple the time.

## Tests

21 tests: self-diff=1.0, deletion → recall, insertion → precision, drift
classified within tolerance, plus `TestScalingExactPath` (sub-quadratic
scaling, 40k-note completion, duplicate-key tie order, tolerance-path
separation). Test spec:
[tests/closed_20260823-191500_w4-diff-tool.md](../../tests/closed_20260823-191500_w4-diff-tool.md).
