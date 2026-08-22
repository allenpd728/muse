# Architecture — how the pieces fit together

The mechanical map: which artifact moves between which tools, and who
validates it at each seam. Read this first, then the per-layer scope docs.

## Artifact flow

```
  .mxl / .mid          IR (beats, midi)         .muse.json            .muse.perf.json         .wav
  (source score)  →   (importer/ir.mjs)   →   (canonical schema) →   (performance doc)  →   (audio)
                      importer/cli.mjs                            interpreter/expand.mjs    player/render.mjs
                      importer/{midi,musicxml}.mjs                interpreter/offline.mjs   tools/play.mjs
                      importer/synthesize.mjs                     (LLM or heuristic)
                                                                  validates: performance.schema.json
                      validates: muse.schema.json
                      + cross-refs + semantics
```

Every arrow is a validation seam: the importer never emits a non-validating
schema; the interpreter never emits a non-validating performance document;
the player consumes only valid performance documents. The harnesses live in
`tools/` (`validate.mjs`, `semantics.mjs`, `refs.mjs`, `test.mjs`).

## The four artifact types

| Artifact | Format | Validated by | Produced by | Consumed by |
|---|---|---|---|---|
| Source score | `.mxl` / `.musicxml` / `.mid` | parser (musicxml-interfaces / @tonejs/midi) | external DAW/notation | importer |
| IR | in-memory JS object | `importer/ir.mjs` `validateIR` | importer parsers | synthesize |
| **Schema** (canonical) | `.muse.json` | `schema/muse.schema.json` + cross-refs + semantics | importer, composer tool, hand edit | interpreter, explorer, composer |
| **Performance** | `.muse.perf.json` (§7) | `schema/performance.schema.json` + perf refs | interpreter (LLM/offline) | player, metrics |
| Audio | `.wav` | — | player | listener, demo |

## Directory map

| Path | What it is |
|---|---|
| `schema/` | JSON Schema files — the machine-checkable contract per spec section |
| `tools/` | `validate.mjs` (CLI), `test.mjs` (harness), `semantics.mjs` (lint), `refs.mjs` (cross-refs), `play.mjs` (schema→audio CLI) |
| `importer/` | source score → IR → schema; `cli.mjs` entry, `fixtures/` test inputs |
| `interpreter/` | `expand.mjs` (LLM harness, provider adapters), `offline.mjs` (deterministic no-key reference expander) |
| `player/` | `render.mjs` — performance doc → WAV (V1 deterministic synthesis) |
| `explorer/` | Vite + React static app (read-only browser + listener tab); deploys via Netlify dev branch preview |
| `benchmark/` | `corpus/` public-domain imports, `metrics.mjs` conformance scoring |
| `examples/` | hand-authored reference schemas (`minimal`, `full`) — the explorer's dev fixtures |
| `docs/` | vision, architecture (this file), pipeline status, per-layer scope docs, demo audio |
| `tests/` | unit/suite files + `open_`/`closed_` test specs per the workflow |
| `blockers/` | open/closed blocker reports needing human input |

## Provider tiers (interpreter)

| Tier | Env | When |
|---|---|---|
| Offline | none | default; deterministic; powers demos + CI |
| Gemini free tier | `MUSE_PROVIDER=gemini`, `GEMINI_API_KEY` | expressive interpretation at no cost |
| Paid adapters | `MUSE_PROVIDER=anthropic|openai` + key | production-quality, BYO key |
| Manual paste | `--manual` (#108) | zero-key fallback, any chat UI |

Usage/error visibility for the API tiers is tracked via the interpreter's
logging — see the usage-tracking task lineage.
