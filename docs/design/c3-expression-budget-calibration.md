# C3 — Expression-budget calibration (design doc, scaffold)

**Phase 3 — Seed authoring. Status: scaffold.**

## Purpose

Delta-analysis-informed budget suggestions per era/style: Classical freedom
in tempo, Romantic in dynamics, chord spread universal (per
[../delta-analysis-plan.md](../delta-analysis-plan.md)). Turns measured
human ranges into seed defaults.

## Dependencies

- **Upstream:** C1 (seed r/w) + delta corpora (Vienna 4x22, Batik/Magaloff,
  Bach chorale corpora; see [../delta-analysis-plan.md](../delta-analysis-plan.md)).
- **Downstream:** proposes budgets that C2 surfaces and humans approve.

## Scope (pin in draft)

- **Inputs:** delta-analysis measurement outputs.
- **Outputs:** era/style budget tables + suggestion engine.
- **Non-goals:** expanding the delta corpus (a standing activity, not this
  task's gate).

## Open questions

- Baroque-era data gap — chorale corpora not yet measured; budgets for
  Baroque remain provisional until measured.

## Acceptance criteria (when promoted to draft)

- Suggested budgets match delta-analysis measured ranges.
