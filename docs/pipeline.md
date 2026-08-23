# Muse build pipeline — work plan and status

The single source of truth for what gets built, in what order, and where it
stands. One task = one GitHub issue, per [TASK_WORKFLOW.md](../TASK_WORKFLOW.md).
Status column is updated by the docs-coherence sweep duty.

## Locked decisions

- **Three-component format.** `.mu` = score (fixed work, our MusicXML) +
  prompt (interpretive space) + plaintext rights manifest. Zip container.
- **MusicXML is the existing roll.** The compressor adapts it; we are not in
  the business of scanning historic documents.
- **The deterministic player is the baseline** — "our MIDI player," free,
  proves the format. **The LLM player is the product** — the musician.
- **Compressor and LLM player are proprietary.** Spec + reference player go
  public at launch. One private repo during development; split at pre-launch.
- **Tools before spec freeze.** The analyzer teaches us what the language
  needs; the diff tool teaches us whether compression works. Spec v1.0 is
  written from evidence, not ahead of it.
- **The corpus is the ratchet.** Bach → Byrd → Schubert → Beethoven 5 →
  Beethoven 9. Each rung gates the next; the Ninth is the v1.0 target.

## Phase 0 — Analysis workbench (tools that teach)

| Task | What it is | Status |
|---|---|---|
| W1 — Event-stream IR | Canonical in-memory event format all tools share: notes (pitch/onset/duration/velocity), tempo map, meter, key, dynamics, parts. Parsers: MusicXML in, MIDI in. | todo |
| W2 — Corpus loader | Loads every [corpus/](../corpus/) file into the IR. Known-answer tests: note counts, part counts per source README. | todo |
| W3 — Analyzer | Pattern detector over the IR: exact repeats, transposed repeats, sequences, mirror/retrograde candidates, ostinati. Outputs per-work statistics + pattern inventory. | todo |
| W4 — Diff tool | Event stream ↔ event stream: recall/precision in tick space. The ground truth for every compression claim. | todo |
| W5 — Visualizer | Piano-roll plots with pattern overlays. Human evaluation aid — the founder reviews what the analyzer claims. | todo |

**Phase 0 done when:** the analyzer has run across all five works and produced
a pattern-frequency report that drives Phase 1 language decisions.

## Phase 1 — Format spec v1.0 (from evidence)

| Task | What it is | Status |
|---|---|---|
| S1 — Event stream format | The decoder↔renderer contract: binary layout, tick resolution, dynamics curves. | todo |
| S2 — Roll encoding | How the fixed score is packed: columnar, delta-encoded, entropy-coded. | todo |
| S3 — Seed encoding | Interpretive parameters, sanctioned ranges, performance philosophy fields. | todo |
| S4 — Language spec | The executable layer: operators (transpose/invert/retro/aug/dim), control flow, assertions. Informed by W3's pattern report. | todo |
| S5 — Container + manifest | Zip layout, plaintext rights manifest, content hashes, signature. | todo |

**Phase 1 done when:** FORMAT_SPEC.md v1.0 is written, with every construct
justified by Phase 0 evidence (a construct without corpus evidence doesn't ship).

## Phase 2 — Deterministic player (the baseline)

| Task | What it is | Status |
|---|---|---|
| P1 — Reference decoder | `.mu` roll stream → event stream. Deterministic, sandboxed, resource-bounded. | todo |
| P2 — Reference renderer | Event stream → audio (soundfont tier). CLI: `muse play file.mu`. | todo |
| P3 — Conformance suite | Golden vectors: (file → event stream) pairs. CI gate. | todo |

**Phase 2 done when:** every corpus `.mu` round-trips through the player and
the diff tool confirms the score reconstructs the source losslessly.

## Phase 3 — Compressor (proprietary)

| Task | What it is | Status |
|---|---|---|
| C1 — Packer | Event stream → score encoding. Lossless round-trip on the whole corpus. | todo |
| C2 — Pattern compressor | W3's detected patterns → language constructs. The AI-in-the-loop: compress → expand → diff → adjust. | todo |
| C3 — Seed authoring | Human-in-loop interpretive annotation (the conductor layer). Founder evaluates by ear against known scores. | todo |
| C4 — Manifest writer | Rights, provenance, AI disclosure, signatures. | todo |

**Phase 3 done when:** the full corpus compresses to `.mu` and expands back
with the diff tool green — Beethoven 9 included.

## Phase 4 — LLM player (the product)

| Task | What it is | Status |
|---|---|---|
| L1 — Expansion harness | `.mu` (roll + seed) → expressive performance. LLM as interpreter, bounded by roll constraints. Generate → validate → fix loop. | todo |
| L2 — Performance renderer | Expressive event stream → audio at sample tier. The "worth listening to" bar. | todo |
| L3 — Model comparison rig | Same `.mu`, different LLMs → different performances. Blind listening evaluation. The "culture" experiment. | todo |

**Phase 4 done when:** one corpus work, rendered by the LLM player, passes
the founder's by-ear evaluation as a musical performance — not a mockup.

## Explicitly not (yet)

- Public spec publication (pre-launch decision)
- Distribution/registry/marketplace
- Neural audio rendering (sample tier first)
- Notation-software and DAW plugins (post-launch)
