# Muse

**An executable music format.** A `.mu` file is the compressed, executable
encoding of a musical work — the roll and the seed in one container. Any
conforming player reads the **roll stream** (the fixed structure: our
MusicXML-class score) for exact mechanical playback; an LLM player reads the
**seed stream** (the interpretive space) and brings the work to life.

> **Status: private development, docs + corpus phase.** The repo holds the
> design documents, the work-tracking process, and the reference corpus.
> Tooling lands per [`docs/pipeline.md`](docs/pipeline.md). Nothing here is
> public-ready; the format spec will be published at launch, not before.

## The product model

MusicXML is the existing roll — the full score, uncompressed. Muse compresses
and adapts it into `.mu`: portable, executable, and carrying the interpretive
space alongside the notes.

```
MusicXML (the existing roll)
    │
    ▼  compressor (proprietary, AI-assisted)
.mu file = roll stream + seed stream + rights manifest
    │
    ├─▶ deterministic player (free, reference) — reads the roll.
    │    "Our MIDI player." Proves the format, verifies encodings.
    │
    └─▶ LLM player (the product) — reads roll + seed.
         "The musician." Brings the work to life.
```

Technology advancing hardware by changing the software: the deterministic
player never changes; the rolls keep getting better.

## The two streams

| Stream | Contains | Read by |
|---|---|---|
| **Roll** | Notes, structure, form, dynamics — the fixed score | Deterministic player |
| **Seed** | Interpretive space: sanctioned ranges, performance philosophy, what may vary | LLM player |

## Components

| Component | Status | Visibility |
|---|---|---|
| Format spec ([FORMAT_SPEC.md](FORMAT_SPEC.md)) | Design draft | Public at launch |
| Reference corpus ([corpus/](corpus/)) | **Acquired** — Bach, Byrd, Schubert, Beethoven 5, Beethoven 9 complete | Public domain sources |
| Compressor (MusicXML → `.mu`) | Not built | Proprietary |
| Deterministic player | Not built | Public at launch |
| LLM player | Not built | **The product — proprietary** |

## The corpus

Five public-domain works in high-quality MusicXML/MIDI, from Bach chorales to
the complete Beethoven 9 — the v1.0 conformance target. See
[corpus/README.md](corpus/README.md).

## Process

Multi-agent task workflow per [TASK_WORKFLOW.md](TASK_WORKFLOW.md): one task
per GitHub issue, label-based states, blockers over guessing. The work plan
lives in [docs/pipeline.md](docs/pipeline.md).

## Principles

1. **Format-first.** The spec is the platform. Everything else is a client.
2. **Determinism is the baseline.** Same file → same roll playback, everywhere.
3. **The seed is the product.** The LLM player grows what the roll fixes.
4. **Composer-owned, rights-carrying.** Plaintext manifest: license,
   provenance, AI disclosure. No artist lookalikes without license.
5. **Own the format, not the models.** LLMs are the utility; Muse is the radio.
