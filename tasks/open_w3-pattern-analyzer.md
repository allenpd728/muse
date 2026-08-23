# W3 — Pattern analyzer

**Status:** open
**Depends on:** W2
**Phase:** 0 (workbench)

## Summary

The pattern detector that teaches us what the format needs. Runs over the IR
and finds: exact repeats, transposed repeats (interval-contour matching),
sequences, mirror/retrograde candidates, ostinati, imitative entries
(polyphonic). Outputs per-work statistics and a pattern inventory.

## Definition of done

- `tools/` analyzer: IR → pattern report (JSON + human-readable summary).
- Detects at minimum: exact repeats, transposed repeats, sequences.
- Runs across the full corpus via W2; produces the pattern-frequency report
  (per work: % of notes covered by each pattern class).
- Report committed as `docs/analysis-report.md` — this document drives Phase 1.
- Scaling: must complete on `corpus/beethoven/beethoven-sym5-mov1.xml`
  (13,675 notes) without superlinear blowup. Beethoven 9 (239k notes) may be
  sampled/sliced; note the approach in the report.
- Test spec written per TASK_WORKFLOW.

## Context

- W2 — corpus loader
- The old importer's O(n³) substring heuristic is the cautionary tale
  (git history: importer/synthesize.mjs). Use suffix structures or bounded
  windows — do not enumerate all substrings.
