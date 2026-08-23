# S4 — Language spec (design doc, scaffold)

**Phase 1 — Format spec. Status: implemented (dev, issue #140).**

## Purpose

The executable layer, if needed: operators (transpose/invert/retro/aug/dim),
control flow, assertions — over the packed score. Whether the corpus demands
a general operator set or a leaner one is a W3 evidence question
(FORMAT_SPEC §8).

## Dependencies

- **Upstream:** W3 pattern report.
- **Downstream:** P1 (decoder semantics), C2-inspired authoring loops.

## Scope (pin in draft)

- **Inputs:** W3 pattern inventory by frequency.
- **Outputs:** spec section + hand-written example programs.
- **Non-goals:** generality for its own sake — a construct without corpus
  evidence doesn't ship (locked decision).

## Open questions

- Operator set: the five classics, more, or fewer.

## Acceptance criteria (when promoted to draft)

- Spec section written; hand-written example programs exercise each shipped
  construct.

## Event log (implementation, 2026-08-23)

- Spec landed as FORMAT_SPEC §5.1. Operator set decided by W3's
  full-corpus report (docs/analysis-report.md): three classes recur in all
  13 corpus files — exact, transposed, ostinato — and ship as
  `ptn_exact` / `ptn_transposed` / `ptn_ostinato`. Invert, retrograde, and
  imitative have zero corpus evidence and are deferred (a construct
  without corpus evidence doesn't ship).
- Program shape: flat list of `{op, region, part?, interval?}` entries,
  half-open tick regions, no nesting. `interval` is a signed string
  (`+2`, `-5`) — sign mandatory.
- Validator: `tools/muse_ops/` (grammar + optional work-bounds check).
  Semantics explicitly out of scope — P1's decoder owns evaluation.
- Hand-written example programs: Bach chorale (three ops), Byrd imitation
  modeled as transposed repeats, Schubert ostinato layer — all in
  `tools/muse_ops/test_ops.py`.
