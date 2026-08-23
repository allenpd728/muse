# W5 — Visualizer (design doc, scaffold)

**Phase 0 — Analysis workbench. Status: scaffold.**

## Purpose

IR + W3 pattern report → piano-roll plots with pattern overlays. Human
evaluation aid: the founder reviews what the analyzer claims before Phase 1
spends it.

## Dependencies

- **Upstream:** W1 (IR); W3 for pattern overlays (plot layer works without).
- **Downstream:** founder review only — not a product surface.

## Scope (pin in draft)

- **Inputs:** IR, optional pattern inventory.
- **Outputs:** static plots (piano-roll), committed or generated on demand.
- **Non-goals:** interactive UI.

## Open questions

- Rendering library choice (matplotlib vs. browser-based).

## Acceptance criteria (when promoted to draft)

- Renders a Bach chorale and a Byrd movement legibly; founder reviews.
