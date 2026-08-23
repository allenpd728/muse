# Frontend explorer — design doc scaffold

**Phase 2.5 — integration. Status: scaffold (awaiting issue + human sign-off; public surface decision deferred).**

## Purpose

A read-only web explorer for the corpus and its artifacts: browse the five works, inspect IR summaries (parts, maps, dynamics, hairpins), run the analyzer's pattern inventory (W3), view W5 piano-roll visualizations, inspect pack stats (S2 ratios), play rendered audio when P2 lands. W5's "human evaluation aid" and the founder's "the ear gates" — made explorable. Deployed via the existing Netlify QA site (`docs/spike` publisher), never production.

## Dependencies

- **Upstream:** W3 (patterns), W5 (visualizer), S2 (stats), P2 (audio later).
- **Downstream:** E2/E3 (the event's public face when it goes public).

## Scope (pin in draft)

- **Inputs:** corpus + generated artifacts (analyzed report, renders).
- **Outputs:** static site under docs/spike/ or a sibling directory; Netlify QA deploy.
- **Non-goals:** authoring (C-series UI — proprietary, separate), live LLM harness (L-series), anything user-account or dynamic (static only).

## Open questions (draft-level)

- Static site vs. tiny JS app? Static + precomputed JSON artifacts fits the QA site.
- Public/private split timing (the QA URL is unlisted but reachable; docs coherence).

## Acceptance criteria

- Founder can open the QA URL, pick any corpus work, see its IR summary + patterns + piano-roll; deploys automatically on dev push.
