# Seed growth harness — design doc scaffold

**Phase 3 — seed authoring (proprietary). Status: scaffold (awaiting sign-off).**

## Purpose

The workbench answers "is the seed holding its landmarks" (regression). It
cannot answer "is the seed **growing**" because the growth channel is
unwired: `tools/muse_probes`'s mockup path is the deterministic L1 stand-in
(flat notes), and the L4 distiller (mockup → revised seed) is never invoked.
The harness closes the loop the probes were always meant to measure:

```
seed (v_n) → mockup (L1, real) → distill (L4) → revised seed (v_n+1)
     ↑                                                    │
     └────────── re-probe: growth report ─────────────────┘
```

One pass = one growth report: did the interpretation traits the seed
declares (budgets, philosophy) actually move the mockup, and did the
distilled revision move them further? The workbench surfaces the growth,
not just the floor.

## What "growth" means measurably

The distiller's `Interpretation` (tools/muse_distill) is the measurable
handle: tempo curve shape + range, velocity mean/pstdev, rubato mean/pstdev,
per-part balance, articulation frequency. Growth per iteration =

| Signal | Improvement reads as |
|---|---|
| velocity_pstdev | rising toward era-typical expressivity (not flat) |
| rubato_pstdev_ms | nonzero where philosophy declares rubato/flexible |
| tempo curve shape | matches philosophy (arch → architectural, wavering → flexible) |
| budget position | tempo defaults converge toward budget center over revisions |
| mockup richness | notes gain attack/release/swell fields the stand-in lacks |

A seed that produces flat-velocity, zero-rubato mockups every pass is not
growing regardless of assertion pass/fail. The harness reports the delta
per iteration so the founder sees trajectory, not snapshots.

## The harness

```
tools/muse_grow/
  grow.py        — one iteration: seed → mockup (L1) → distill (L4) → delta
                   (delta carries an `expansion` entry: wall-clock
                   expansion_time_ms keyed by operation tag, with
                   variation_point_count + note_count — G4/#252)
  compare.py     — delta vs prior iteration's delta → growth report
  cli.py         — muse-grow <seed.yaml> [--prior <delta.json>]
```

- **L1 input**: the real mockup generator when it exists; until then the
  harness marks every mockup `stand-in: true` and the growth report says so
  (growth cannot be measured on a flat mockup — that is itself a finding).
- **L4 input**: `muse_distill.seed_revision(mockup)` → delta dict
  (interpretation + provenance). No auto-apply; the harness compares deltas.
- **Mockup persistence (S3.8b, #254):** `--mockup-out` writes the
  producing mockup next to the seed revisions (`seeds/<work>.<rev>.mockup.json`)
  carrying `provenance.seed_hash` (the seed's bytes hash, L1.10); the
  distilled delta's `provenance.extends` names that mockup's bytes and
  `operation` stamps `muse_distill@1`. The lineage walker (S3.8a) then
  resolves the mockup hop. First live chain: `seeds/bwv227.1.v3.seed.yaml`
  → `bwv227.1.v2.mockup.json` → `bwv227.1.v2.seed.yaml` → root.
- **Growth report**: per-trait delta between iteration n and n-1, with a
  verdict per trait (growing / flat / regressing).

## Tasks

| Task | Scope | Blocked by |
|---|---|---|
| **G1 — Growth harness** ([#203](https://github.com/allenpd728/muse/issues/203)) | `tools/muse_grow/`: L1→L4→delta→compare pipeline + growth report JSON | L1 generate loop (real); stand-in marked until then |
| **G2 — Workbench growth view** ([#204](https://github.com/allenpd728/muse/issues/204)) | growth report rendered per seed (trait trajectories across iterations) | G1 |
| **G3 — Iteration fixtures** ([#205](https://github.com/allenpd728/muse/issues/205)) | two committed seed revisions + their deltas so G1's compare has known-answer tests | G1 |
| **G4 — Expansion-time logging** ([#252](https://github.com/allenpd728/muse/issues/252)) | log `expansion_time_ms` per `operation` tag against `(variation_point_count, note_count)` per `grow_one` call — measurement toward a future expansion-cost estimate (proposal: [lineage chain](proposal-lineage-chain.md) §2.4) | S3.7 ([#248](https://github.com/allenpd728/muse/issues/248)) | **done** (#252, 2026-08-26: the delta carries an `expansion` entry — wall-clock build time keyed by the seed's `provenance.operation` (default `muse_grow@1`), with variation-point and note counts; error paths carry no phantom timing) |

G1 is the foundation; G2/G3 decompose from it. G4 is instrumentation
riding the harness, not a new subsystem.

## Explicitly not (yet)

- Auto-applying distilled revisions (L4 stays human-reviewed, per its design)
- LLM-driven mockup generation (the real L1 loop is its own task line)
- Cross-work transfer (seed on work A informing seed on work B)
