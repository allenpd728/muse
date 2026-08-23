# E2E chain harness — design doc scaffold

**Phase 2.5 — integration. Status: scaffold (awaiting issue + human sign-off).**

## Purpose

One harness that walks the full pipeline: `corpus source → IR (W1) → packed roll (S2) → container (S5) → decoder (P1) → event stream → renderer (P2) → WAV → sanity checks`, for every corpus file. Each task in the chain is proven individually; this proves they compose. Chains are the natural place to smoke-test determinism (pack twice, decode twice, same bytes) and catch interface drift across the proprietary/public seam.

## Dependencies

- **Upstream:** W1 (IR), W2 (loader), S2 (packer), S5 (container), P1 (decoder), P2 (renderer).
- **Downstream:** CI (P3), E-series (event readiness).

## Scope (pin in draft)

- **Inputs:** corpus registry (the same five works, same files).
- **Outputs:** per-work chain result (pass/fail per stage), chain report artifact, failing stage isolated to a named task.
- **Non-goals:** LLM-player (L-series) integration — that is a separate chain once L1 exists; frontend serving (that's the explorer task).

## Open questions (draft-level)

- Stage granularity: do we chain pack→unpack only (cheap), or full container round-trip with manifest verification?
- Determinism check budget: full corpus twice (~5min) vs. one tier twice (~30s).

## Acceptance criteria

- Chain runs end-to-end on the whole registry without manual steps; failure names the stage; deterministic by construction (two runs → identical artifacts).
