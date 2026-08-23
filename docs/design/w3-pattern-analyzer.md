# W3 — Pattern analyzer design doc

**Phase 0 — Analysis workbench. Status: draft (was scaffold).**

Evidence base: [../literature-review-w1.md](../literature-review-w1.md) §3,
§6 — algorithm pick: SIATEC/NCD-class via Ostinato, rhythmic complement via
RegularTimeInterval_Patterns_Discovery; scale plan for the 239k-note Ninth.

## Purpose

IR → pattern report: exact repeats, transposed repeats, sequences,
mirror/retrograde candidates, ostinati, imitative entries, plus per-phrase
delta curves (the open delta-analysis question). The evidence engine for
Phase 1: a construct without corpus evidence doesn't ship.

## Dependencies

- **Upstream:** W1 (IR), W2 (loaded corpus).
- **Downstream:** S1–S5 (evidence), W5 (overlays), C3 (era budgets).

## Interface (draft)

```
muse-analyze <work>         → doc: pattern inventory + per-phrase delta
muse-analyze --all          → full-corpus report → docs/analysis-report.md
```

Pattern classes map to SIATEC-style detection; rhythm algorithms handle
ostinati/sequences where pitch-invariance matters. Output format: a
structured report (JSON + markdown) — S-composing agents consume the JSON,
W5 renders the markdown.

## Scope

- **Inputs:** IR from W2.
- **Outputs:** structured report; `docs/analysis-report.md` produced.
- **Non-goals:** compression itself (S2 consumes patterns), human-readable
  presentation (W5).

## Open questions (draft-level)

- Compute plan for Beethoven 9: SIATEC-C or sampling; W3 must declare the
  ladder-budget per corpus tier before the Ninth's pass.
- Whether delta curves live in this tool or a sibling module: initial
  draft — same tool, separate CLI flag.

## Acceptance criteria (when promoted to draft)

- Runs on the full corpus (registry works); `docs/analysis-report.md`
  committed; test specs open per TASK_WORKFLOW.
