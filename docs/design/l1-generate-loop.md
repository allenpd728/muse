# L1 generate loop — design doc scaffold

**Phase 4 — Mockup harness (the product). Status: scaffold (awaiting sign-off).**

## Purpose

The real L1: `score + seed → LLM → mockup at full DNA density`. What exists
today (`tools/muse_mockup/`, issue #173) is the schema and the validator; what
does not exist is the *generate* half. The deterministic stand-in
(`MOCKUP_FN` in probes/grow) proves the seam; it does not generate
interpretation. This is the product's core loop: the LLM does the session
work (tempo map, dynamic curves, per-note velocities, balance, chord spread,
attack/release, swell) inside the seed's sanctioned ranges, the validator
catches violations, and a bounded retry loop fixes or fails loudly.

## The loop

```
seed + score (IR)
   → prompt assembly (S3 fields + work structure + budgets)
   → LLM generation (provider adapter, free-tier first)
   → mockup JSON (W7 schema: tempo_map, curves, notes with devices)
   → validate (C1: schema → assertions → budgets)
   → fail? → fix prompt with the violation → retry (bounded, e.g. 3)
   → pass → mockup artifact
```

## Components to build

| Component | What it is | Status |
|---|---|---|
| **Mockup schema finalization** | W7's scaffold → committed schema. The spike JSONs (mockup-v1/v2/v3) are the evidence base; per-note devices (chord_spread_ms, attack_sec, swell, legato_overlap_ms) are first-class fields | scaffold only |
| **Provider adapter** | one pluggable interface `generate(prompt) → json`; Gemini free-tier first (the spike-era precedent), manual-paste mode when no key. No training, no fine-tuning — stock model steered by prompt (pipeline locked decision) | missing |
| **Generate → validate → fix loop** | assemble prompt from seed + work; call provider; validate via C1; on violation, re-prompt with the failure and retry (bounded) | missing |
| **Prompt templates** | S3 seed fields + era budgets + work summary (parts, maps, pattern inventory) → the LLM's instructions | missing |

## Constraints (from locked decisions)

- **No model training in the product path** — stock swappable model, prompt-only steering.
- **Assertions bound the generation** — every mockup validates against the work's assertions (register, tempo_bounds, must_contain, form) before it's accepted; a violation is a retry, never a silent pass.
- **Determinism is the baseline** — the LLM layer is where variation lives; the score stays untouched (fidelity guard).
- **Bounded retries** — no infinite loops; a mockup that can't validate after N tries fails loudly with the violation record.

## Evidence base

- Spike mockups: `docs/spike/mockup-v1/v2/v3.json` (hand-authored, prove the schema)
- W3 pattern inventory: what motifs the LLM should preserve/develop
- Delta analysis: era budgets (measured ranges the generation must stay inside)

## Proposed tasks (not started)

| Task | Scope | Blocked by |
|---|---|---|
| **L1.1 — Mockup schema finalize** | W7 scaffold → committed schema + validator (fields: tempo_map, curves, per-note devices); W4-validated example | W7 (scaffold exists) |
| **L1.2 — Provider adapter** | pluggable generate interface; Gemini adapter (free tier) + manual-paste fallback; deterministic on recorded fixtures | none |
| **L1.3 — Generate/validate/fix loop** | prompt assembly → provider → validate (C1) → fix-retry (bounded) → mockup | L1.1, L1.2 |
| **L1.4 — Integration tests** | one corpus work end-to-end (recorded LLM fixture, no live call); validates; growth harness picks it up | L1.3 |

L1.1 and L1.2 are parallel-safe; L1.3 needs both; L1.4 closes it.

## Explicitly not (yet)

- Fine-tuning or training (explicit escape hatch only, plan B)
- Live-LLM tests in CI (recorded fixtures only; live runs are manual)
- Multi-provider comparison (that's L3, already landed separately)
