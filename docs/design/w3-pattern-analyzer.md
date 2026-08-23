# W3 — Pattern analyzer (design doc, scaffold)

**Phase 0 — Analysis workbench. Status: scaffold.**

## Purpose

IR → pattern report: exact repeats, transposed repeats, sequences,
mirror/retrograde candidates, ostinati, imitative entries. Per-work
statistics + inventory. The evidence engine for Phase 1: no spec construct
ships without this report justifying it. Also the home of per-phrase delta
curves (the open delta-analysis question).

## Dependencies

- **Upstream:** W1 (IR), W2 (corpus access).
- **Downstream:** S1–S5 (evidence), W5 (overlays), C3 (era budgets).

## Scope (pin in draft)

- **Inputs:** IR from W2.
- **Outputs:** `docs/analysis-report.md` (produced), structured pattern
  inventory.
- **Non-goals:** compression itself (S2 consumes patterns), human-readable
  presentation (W5).

## Open questions

- Which pattern classes earn language constructs vs. mere packing hints.

## Acceptance criteria (when promoted to draft)

- Runs on the full corpus; docs/analysis-report.md committed.
