# W2 — Corpus loader

**Status:** open
**Depends on:** W1
**Phase:** 0 (workbench)

## Summary

A loader that walks `corpus/` and produces the IR for every work, with
known-answer tests per file. This is the ratchet: every later tool runs
against the corpus through this loader.

## Definition of done

- `tools/` loader: corpus path → IR (uses W1 parsers), all five works.
- Known-answer assertions per corpus/README.md: note counts, part counts,
  dynamics counts where measured (Beethoven 5 mov 1: 431; Beethoven 9: 11,931).
- CLI: `node tools/corpus.mjs <work>` prints IR summary stats.
- Test spec written per TASK_WORKFLOW.

## Context

- corpus/README.md — the source registry and measured counts
- W1 — the IR this loader produces
