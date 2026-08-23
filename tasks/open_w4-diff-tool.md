# W4 — Diff tool

**Status:** open
**Depends on:** W1
**Phase:** 0 (workbench)

## Summary

Event stream ↔ event stream comparison in tick space: recall, precision, and
a readable mismatch report. This is the ground truth for every compression
claim — the compress → expand → diff loop does not exist without it.

## Definition of done

- `tools/` diff: two IRs → { recall, precision, mismatches[] } with
  configurable tick tolerance.
- Handles part-aligned comparison (notes matched within their part).
- CLI: `node tools/diff.mjs <a> <b>` (accepts corpus paths or IR dumps).
- Known-answer test: an IR diffed against itself scores 1.0/1.0; a note
  removed drops recall predictably.
- Test spec written per TASK_WORKFLOW.

## Context

- W1 — the IR being compared
- This tool becomes the W5 visualizer's diff overlay source, the Phase 3
  compression loop's scoring function, and the Phase 2 conformance gate.
