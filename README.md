# Muse

**An executable music format.** A `.mu` file packages a musical work as three
components: the **score** (the fixed work — our compressed MusicXML), the
**prompt** (the interpretive space), and the **manifest** (plaintext rights).
Any conforming player reads the score for exact mechanical playback; an LLM
player reads score + prompt and brings the work to life — slowly,
deliberately. A performance is an event, not a render.

> **Status: private development.** Format spec, tooling, and corpus live on
> `dev`; deterministic player (P1/P2) and LLM-side harnesses are landed and
> tested. Nothing here is public-ready; the format spec will be published at
> launch, not before.

## The product model

MusicXML is the existing roll — the full score, uncompressed. Muse compresses
and adapts it into `.mu`: portable, executable, and carrying the interpretive
space alongside the notes.

```
MusicXML (the existing roll)
    │
    ▼  compressor (proprietary, AI-assisted)
.mu file = score + prompt + manifest
    │
    ├─▶ deterministic player (free, reference) — reads the score.
    │    "Our MIDI player." Proves the format, verifies encodings.
    │
    └─▶ LLM player (the product) — reads score + prompt, produces a
         mockup (the session file: tempo map, curves, balance), rendered
         through samples. "The musician." A performance is an event.
```

Technology advancing hardware by changing the software: the deterministic
player never changes; the rolls keep getting better.

## The components

| Component | Contains | Read by |
|---|---|---|
| **Score** | Notes, structure, form, dynamics — the fixed work | Deterministic player |
| **Prompt** | Interpretive space: sanctioned ranges, performance philosophy, what may vary. Authored from any source (MusicXML, DAW session, MIDI) via the shared IR. | LLM player |
| **Manifest** | License, provenance, AI disclosure, hashes | Anyone — plaintext |

## Components

| Component | Status | Visibility |
|---|---|---|
| Format spec ([FORMAT_SPEC.md](FORMAT_SPEC.md)) | Design draft | Public at launch |
| Reference corpus ([corpus/](corpus/)) | **Acquired** — Bach, Byrd, Schubert, Beethoven 5, Beethoven 9 complete | Public domain sources |
| Compressor (MusicXML → `.mu`) | **Landed** (S2 [tools/muse_roll](tools/muse_roll/); container S5 [tools/muse_mu](tools/muse_mu/); seed S3 series through #147) | Proprietary |
| Deterministic player | **Landed** (P1 [tools/muse_decode](tools/muse_decode/); renderer P2 [tools/muse_play](tools/muse_play/)) | Public at launch |
| LLM player | In progress — session-file harness L1 [tools/muse_mockup](tools/muse_mockup/), renderer L2 [tools/muse_render](tools/muse_render/), A/B rig L3 [tools/muse_compare](tools/muse_compare/), distiller L4 [tools/muse_distill](tools/muse_distill/) | **The product — proprietary** |

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
2. **Determinism is the baseline.** Same file → same score playback, everywhere.
3. **The prompt is the product.** The LLM player grows what the score fixes.
4. **Composer-owned, rights-carrying.** Plaintext manifest: license,
   provenance, AI disclosure. No artist lookalikes without license.
5. **Own the format, not the models.** LLMs are the utility; Muse is the radio.
