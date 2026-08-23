# W2 — Corpus loader design doc

**Phase 0 — Analysis workbench. Status: draft (was scaffold).**

Evidence base: W1's draft pins the IR and conformance table; this loader
consumes it. W1 is itself a draft, so W2's draft depends on W1's final form
only in detail, not in shape.

## Purpose

Load every [corpus/](../../corpus/) file through the W1 parsers into IR,
with an assertion-checked CLI summary. The ratchet's front door: every later
tool recovers works through this loader, never through ad-hoc parsing.

## Dependencies

- **Upstream:** W1 (draft).
- **Downstream:** W3 (analysis), W5 (rendered views).

## Interface (draft)

```
muse-corpus list            → registry table: work, files, source_format
muse-corpus load <work>     → IR summary: parts, notes, maps coverage
muse-corpus check           → known-answer assertions across registry
```

`check` is the CI gate: it fails loudly unless every corpus README row
parses with its pinned (parts, notes) counts. W1's conformance table is the
pin set; the loader registry reuses it.

## Scope

- **Inputs:** corpus registry ([../../corpus/README.md](../../corpus/README.md)),
  W1 parsers.
- **Outputs:** loaded IR per work + assertion-checked summary CLI.
- **Non-goals:** corpus acquisition (done), license-checking beyond the
  registry; caching/serialization (S1's domain).

## Open questions (draft-level)

- `source_format=midi` propagation: loader metadata includes W1's
  `meta.source_format` flag so W3/W5 can annotate inference risk. Draft
  position: propagate; W3's report marks it.
- Whether `check` belongs in CI yet (P3 owns CI; W2's CLI is pre-CI
  smoke).

## Acceptance criteria (when promoted to draft)

- All five works load; known-answer assertions (note/part counts) green;
  loud failure on malformed/corpus-drift inputs; test specs open per
  TASK_WORKFLOW.
