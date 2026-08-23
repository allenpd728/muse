# C5 — Baroque delta measurement (design doc, scaffold)

**Phase 3 — Seed authoring (sub-task; measurement executed when W4 exists).
Status: scaffold.**

## Purpose

C3's budgets have Classical (Vienna 4x22) and Romantic (Magaloff) anchors
but no measured Baroque anchor. This sub-task runs the delta-analysis
vocabulary (chord spread, duration spread, velocity spread, IOI variance)
across Baroque corpora (chorales + polyphony), closing the era gap.

## Dependencies

- **Upstream:** W4 (diff/measurement tool) + chosen Baroque corpora;
  conceptually independent of C1.
- **Downstream:** C3 (era budgets), W3 (into its per-phrase delta report).

## Scope (pin in draft)

- **Inputs:** aligned Baroque corpora via ASMD/humdrum sources.
- **Outputs:** era-budget table + measurement report.
- **Non-goals:** corpus-format normalization (ASMD handles it); a full
  $-splined budget model (C3 owns).

## Open questions

- Which Baroque corpora — aligned anchor or free chorale corpora; access
  path via [../literature-review-w1.md](../literature-review-w1.md) §4.

## Acceptance criteria (when promoted to draft)

- Baroque delta table cited by C3; measurement report committed.
