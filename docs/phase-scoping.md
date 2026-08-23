# Phase scoping — the full map before tasks

**Date:** 2026-08-23. **Purpose:** Scope every remaining phase so design docs
and agent tasks are written against a complete plan, not discovered
mid-flight. This document is the source for `docs/pipeline.md` task
decomposition. No tasks filed until this is signed off.

## The five transitions (from the product model)

Every piece of work serves one of these transitions:

| # | Transition | Tool | Phase |
|---|---|---|---|
| T1 | Source → IR | Parser (MusicXML, MIDI, later DAW XML) | 0 (done for spike) |
| T2 | IR → seed | Seed authoring workbench | 3 |
| T3 | score + seed → mockup | Mockup harness (LLM session work) | 4 |
| T4 | mockup → audio | Renderer (sfizz + SFZ) | 4 |
| T5 | mockup → new seed | Distiller | 5 |

## Phase 0 — Analysis workbench (tools that teach)

**Goal:** the IR and the instruments that every later phase consumes.

| Task | What it is | Done when |
|---|---|---|
| W1 — Event-stream IR | Canonical in-memory event format: notes (pitch/onset/duration/velocity), parts, tempo/meter/key maps, dynamics, articulations. Parsers: MusicXML, MIDI. Integer ticks only. | Parses corpus; known-answer tests pass (note/part counts per corpus/README) |
| W2 — Corpus loader | corpus/ → IR for all five works, via W1. CLI summary stats. | All five works load; assertions green |
| W3 — Pattern analyzer | IR → pattern report: exact/transposed repeats, sequences, mirror/retro candidates, ostinati, imitative entries. Per-work statistics. | Runs on full corpus; produces docs/analysis-report.md |
| W4 — Diff tool | IR ↔ IR comparison: recall/precision in tick space, tolerance-configurable. The ground truth. | Self-diff = 1.0; mutation tests behave |
| W5 — Visualizer | IR + pattern report → piano-roll plots with pattern overlays. | Renders chorale + Byrd legibly; founder reviews |

**Dependencies:** W1 → W2 → W3 → W5; W1 → W4.
**Not started.** Spike scripts (tools/spike/) are disposable prototypes, not this.

## Phase 1 — Format spec v1.0 (from evidence)

**Goal:** pin the `.mu` format from Phase 0 + delta-analysis evidence.

| Task | What it is | Done when |
|---|---|---|
| S1 — Event stream format | The decoder↔renderer contract: binary layout, tick resolution, dynamics curves. | Spec section written + golden vectors |
| S2 — Score encoding | Packing scheme: columnar, delta-encoded, entropy-coded. | Round-trips corpus losslessly |
| S3 — Seed format | The prompt: sanctioned ranges, philosophy fields, expression budgets, assertions. Calibrated from delta analysis. | Spec section + example seed validates |
| S4 — Language spec | Executable layer: operators (transpose/invert/retro/aug/dim), control flow, assertions. | Spec section + hand-written example programs |
| S5 — Container + manifest | Zip layout, plaintext rights manifest, hashes, signature. | Spec section + manifest validator |

**Dependencies:** all on W-series evidence; S1–S5 can run in parallel once W3 lands.
**Gate:** spec v1.0 written FROM evidence; no speculative constructs.

## Phase 2 — Deterministic player (the baseline)

**Goal:** the free reference implementation — decode + render, no AI.

| Task | What it is | Done when |
|---|---|---|
| P1 — Reference decoder | `.mu` score → event stream. Deterministic, sandboxed, resource-bounded. | Conformance vectors pass byte-exactly |
| P2 — Reference renderer | Event stream → audio (soundfont tier). CLI: `muse play file.mu`. | Any conforming `.mu` renders audibly |
| P3 — Conformance suite | Golden vectors: `.mu` → event stream pairs. CI gate. | Suite runs in CI; gates merges |

**Dependencies:** S1–S2 (score format), S5 (container).
**Not the product** — the baseline that proves the format.

## Phase 3 — Seed authoring (the craft, proprietary)

**Goal:** the workbench where humans + AI author seeds. The product's core craft.

| Task | What it is | Done when |
|---|---|---|
| C1 — Seed format implementation | S3's spec → working reader/writer. | Reads/writes valid seeds; validates against S3 |
| C2 — AI-assisted authoring | LLM analyzes IR → proposes seed (budgets, philosophy, variation points). Human reviews, edits, approves. | Authors a valid seed for one corpus work |
| C3 — Expression-budget calibration | Delta-analysis-informed budget suggestions per era/style. | Budgets match delta-analysis ranges |
| C4 — Assertion authoring | Human writes constraints (must_contain, register, form) per work. | Assertions validate against mockups |

**Dependencies:** S3 (seed format), W4 (diff for validation), delta analysis.
**This is the workshop.** The founder's ear is the quality gate.

## Phase 4 — Mockup harness + renderer (the product)

**Goal:** the LLM does session work → mockup → audio. The product path.

| Task | What it is | Done when |
|---|---|---|
| L1 — Mockup harness | score + seed → LLM → mockup (full DNA density). Generate → validate → fix loop, bounded retries. | Produces a complete mockup for one corpus work |
| L2 — Performance renderer | Mockup → audio via sfizz + SFZ samples (SSO/VPO tier). The "worth listening to" bar. | Renders the mockup audibly |
| L3 — Model comparison rig | Same score+seed, different LLMs → different mockups. Blind A/B listening. | Produces comparable renders from 2+ models |
| L4 — Distiller | Mockup → extracted interpretation → seed revision. The learning loop. | Distills a mockup into a seed delta |

**Dependencies:** C1–C4 (seeds to consume), S1 (event stream), P2 (renderer base).
**The product.** L1+L2 are the core; L3+L4 are the differentiation.

## Phase 5 — The event (the unveiling)

**Goal:** the public performance. Deferred until Phase 4 produces one
concert-worthy work.

| Task | What it is | Done when |
|---|---|---|
| E1 — The work | One corpus work, fully seeded + mocked + rendered at concert quality | Founder's ear approves |
| E2 — The venue | Concert hall, projection, the "giant computer" staging | Event planned |
| E3 — The recording | Document the event | Published |

**Dependencies:** L1–L4 producing concert-tier output.

## The dependency graph

```
W1 → W2 → W3 → W5
W1 → W4
W3 → S1–S5 (evidence)
S1,S2,S5 → P1 → P2 → P3
S3 → C1 → C2 → C3 → C4
C1–C4 + S1 + P2 → L1 → L2 → L3 → L4
L1–L4 → E1 → E2 → E3
```

## What this scoping settles

- **17 tasks across 6 phases** (up from 15 — added C1–C4 as separate tasks,
  L4 distiller, E-series for the event).
- **The critical path:** W1 → W3 → S3 → C1 → C2 → L1 → L2. Everything else
  is parallel or later.
- **The spike is closed** (docs/spike-results.md); its lessons feed C2 and L1.
- **No new model training** anywhere in the graph (locked constraint).
