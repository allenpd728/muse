# C3 — Expression-budget calibration (design doc)

**Phase 3 — Seed authoring. Status: implemented (2026-08-23, #175 →
[tools/muse_budgets](../../tools/muse_budgets/)).**

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

## Event log (implementation, 2026-08-23)

- **Baroque measured** on music21's public-domain `bach` chorale corpus
  (192 accessible, 93 measured IOI-spread values): bound pstdev ≤0.65,
  provisional = False.
- **Classical/romantic marked provisional** — Vienna 4x22 / Batik /
  Magaloff corpora unreachable from this sandbox (GitHub search returns
  nothing, direct corpus pulls 404; delta-analysis-plan notes them as
  pending data). Uplink follow-up is C5's deferred sub-task.
- **C2 wires in** via `muse_author.author._propose` — `from muse_budgets
  import suggest`; middle-bpm = (min+max)/2 where formerly tempo_quick=96
  was hardcoded (deterministic default aligned with budgets). Proposals
  carry `era_budget` on the seed dict.
- **PyYAML needed** on the CLI path (`muse_author` end-to-end CLI
  validates `pyyaml`) — install via pip.
