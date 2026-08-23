# W5 — Visualizer design doc

**Phase 0 — Analysis workbench. Status: draft (was scaffold).**

## Purpose

IR + optional W3 pattern report → piano-roll plots with pattern overlays.
Human evaluation aid: the founder reviews what the analyzer claims before
Phase 1 spends it.

## Dependencies

- **Upstream:** W1 (IR); W3 for pattern overlays (plot layer works without).
- **Downstream:** founder review only — not a product surface.

## Interface (draft)

```
muse-viz <work> [--patterns report.json]
  → output dir with plot images (PNG)
```

Renderer choice settled at draft: matplotlib (scriptable, no runtime dep);
browser-based remains an option if interactivity ever returns.

## Scope

- **Inputs:** IR; optional W3 pattern inventory.
- **Outputs:** static plots (piano-roll), committed or generated on demand.
- **Non-goals:** interactive UI.

## Open questions (draft-level)

- Legibility floor: full-orchestra plots (52 parts in Beethoven 9) need
  per-part-thinning rules; draft position: per-part alpha-scaled overlay of
  note counts, parts selectable via CLI.

## Acceptance criteria (when promoted to draft)

- Renders a Bach chorale and a Byrd movement legibly; founder reviews;
  test specs open per TASK_WORKFLOW.
