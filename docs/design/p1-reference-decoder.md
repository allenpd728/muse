# P1 — Reference decoder (design doc, scaffold)

**Phase 2 — Deterministic player. Status: scaffold.**

## Purpose

`.mu` roll → event stream. Deterministic, sandboxed, resource-bounded; no
I/O, no clock. The free baseline that proves the format; conformance vectors
byte-exact.

## Dependencies

- **Upstream:** S1 (stream contract), S2 (score encoding), S5 (container).
- **Downstream:** P2 (renders its output), all L-series (its stream is the
  baseline seam).

## Scope (pin in draft)

- **Inputs:** container + score encodings.
- **Outputs:** decoder CLI/library emitting S1 streams.
- **Non-goals:** any intelligence (locked: the decoder stays dumb), audio
  (P2).

## Open questions

- Resource-bound policy (step cap, memory cap values).

## Acceptance criteria (when promoted to draft)

- Conformance vectors pass byte-exactly; invalid input fails loudly, never
  hangs.
