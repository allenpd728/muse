# W5 — Visualizer

**Status:** open
**Depends on:** W2, W3
**Phase:** 0 (workbench)

## Summary

Piano-roll plots with pattern overlays — the human-evaluation aid. The
founder reviews what the analyzer claims by eye against scores he knows.
Trust in W3's output is earned here.

## Definition of done

- `tools/` visualizer: IR (+ optional W3 pattern report) → PNG/SVG piano roll.
- Pattern overlays: detected repeats/sequences drawn as aligned spans.
- Renders one full Bach chorale movement and one Byrd movement legibly;
  larger works render per-part or per-section.
- At least one founder review session held; notes captured in
  `docs/analysis-report.md`.
- Test spec written per TASK_WORKFLOW.

## Context

- W2 — corpus loader
- W3 — pattern analyzer (provides overlay data)
- The founder's by-eye evaluation is a standing ground rule (AGENTS.md).
