# P3 — Conformance suite (design doc, scaffold)

**Phase 2 — Deterministic player. Status: scaffold.**

## Purpose

Golden vectors: `.mu` → event stream pairs, run in CI as a merge gate. The
objective definition of "conforming decoder."

## Dependencies

- **Upstream:** P1 (P2 for render smoke).
- **Downstream:** CI gate for everything after P-series lands.

## Scope (pin in draft)

- **Inputs:** corpus `.mu` files, W4-generated goldens.
- **Outputs:** CI job + vector store.
- **Non-goals:** work-conformance (assertions over sanctioned space) — that
  is L1/C4 territory.

## Open questions

- Vector storage format (binary streams in git vs. regenerated).

## Acceptance criteria (when promoted to draft)

- Suite runs in CI; gates merges.
