# Blocker — W1 issue filing: needs founder sign-off on the phase map

**Task attempted:** W1 — Event-stream IR (design doc currently `draft`,
[`docs/design/w1-event-ir.md`](../docs/design/w1-event-ir.md)). The issue
cannot be filed.

## What is missing

Only a **decision**, not information: the repo's own gating conventions
forbid filing the W1 issue until two sign-offs land. Specifically:

- [`docs/phase-scoping.md`](../docs/phase-scoping.md) header: “No tasks
  filed until this is signed off.”
- [`docs/design/index.md`](../docs/design/index.md) maturity ladder:
  “Issues get filed only against approved drafts.”
- PR #122 (open, `review` → `main`) body: “Approve + merge = the vision,
  plan, corpus, and process above are ratified and Phase 0 issues get
  filed.”

W1 is uniquely unblocked *technically* — zero upstream dependencies, draft
complete, known-answer conformance table pinned, literature review evidence
linked — and uniquely blocked *procedurally*: it is the first issue, so the
sign-off gate applies to it and nothing else.

## What I tried and why it is insufficient

- The phase map (`docs/phase-scoping.md`) was reconciled into
  `docs/pipeline.md` (the earlier contradiction — C-series meaning two
  different things in two docs — is resolved; committed on `review`).
- All 24 design scaffolds exist with dependency links (`docs/design/`);
  W1–W5 are promoted to draft, with W1 the critical-path head.
- A literature review (`docs/literature-review-w1.md`) was taken pre-W1.

None of that substitutes for the founder's sign-off, which is the
deliberate human gate.

## Needed to unblock (either suffices)

1. Sign off on the phase map (PR #122 merge or explicit approval), **or**
2. Explicitly authorize filing W1 ahead of the merge as an exception.

Once either lands: file the W1 issue from
[`docs/design/w1-event-ir.md`](../docs/design/w1-event-ir.md), label it
`status:available`, and Phase 0's multi-agent workflow begins (W2–W5 queue
behind it per the index's draft-of-draft chain).
