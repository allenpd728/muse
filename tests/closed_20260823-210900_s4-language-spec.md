# Test spec — S4 language spec (issue #140)

Written by the completing agent per TASK_WORKFLOW step 6. S4 landed with 17
tests (`cd tools/muse_ops && python -m pytest`, <1s).

## Landed coverage (tools/muse_ops/test_ops.py)

- **Operator table:** the three shipped ops pinned; all four deferred ops
  (invert, retro, imitative, transpose) rejected as unknown.
- **Entry grammar:** unknown keys, region shape, empty/negative regions,
  signed-interval requirement on ptn_transposed, part-type check,
  error messages index the failing entry.
- **Bounds:** region-vs-work-duration check; unchecked without a work.
- **Example programs:** Bach chorale (three ops; the spec's acceptance
  criterion), Byrd imitation modeled as transposed repeats, Schubert
  ostinato layer.

## Gaps for a `Tests:` follow-up

1. **Semantics harness.** The validator is grammar-only by design. When P1
   implements evaluation, pin operator semantics through golden vectors
   (program → event stream).
2. **Evidence re-runs.** If W3's analyzer gains a mirror/retrograde class,
   the operator table flip should be mechanical: re-run the report, compare
   table, promote/defer — pin that workflow in one test against
   docs/analysis-report.md.
3. **Program↔seed interplay.** Seed variation regions (S3.4) overlap program
   regions conceptually; pin precedence when C2 authors both (eval rule:
   operators before seed parameters, per FORMAT_SPEC §5 evaluation order).

## How to run

```bash
cd tools/muse_ops && python -m pytest
```
