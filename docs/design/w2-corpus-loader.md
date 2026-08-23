# W2 — Corpus loader (design doc, scaffold)

**Phase 0 — Analysis workbench. Status: scaffold.**

## Purpose

Load every [corpus/](../../corpus/) file into the W1 IR, with CLI summary
statistics. The ratchet's front door: every later tool consumes corpus works
through this loader, not through ad-hoc parsing.

## Dependencies

- **Upstream:** W1 (IR + parsers).
- **Downstream:** W3 (analysis), W5 (rendered views).

## Scope (pin in draft)

- **Inputs:** corpus registry (corpus/README), W1 parsers.
- **Outputs:** loaded IR per work + assertion-checked summary CLI.
- **Non-goals:** corpus acquisition (done), license-checking beyond the
  registry.

## Open questions

- Whether Byrd MIDI-only inference flags propagate to loader metadata.

## Acceptance criteria (when promoted to draft)

- All five works load; known-answer assertions (note/part counts) green.
