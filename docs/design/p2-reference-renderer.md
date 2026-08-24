# P2 — Reference renderer (design doc)

**Phase 2 — Deterministic player. Status: implemented (2026-08-24, #198 →
[tools/muse_play](../../tools/muse_play/)).**

## Purpose

Event stream → audio, soundfont tier (FluidSynth-class). CLI:
`muse play file.mu`. The renderer-side proof of the S1 contract; the seam L2
later lives above.

## Dependencies

- **Upstream:** S1 (stream format).
- **Downstream:** P3 (suite exercises it), L2 (sample-tier renderer base).

## Scope (pin in draft)

- **Inputs:** S1 event stream.
- **Outputs:** WAV/CLI playback.
- **Non-goals:** sample-tier quality (L2), LLM anything.

## Open questions

- Which GM soundfont ships as reference (license-compatible).

## Acceptance criteria (when promoted to draft)

- Any conforming `.mu` renders audibly offline.
