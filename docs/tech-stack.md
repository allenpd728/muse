# Tech stack — existing software, protocols, and specs in use

The single index of what Muse borrows vs. builds. Cross-linked from
[prior-art-spike.md](prior-art-spike.md) (renderer/component intel),
[literature-review-w1.md](literature-review-w1.md) (IR/compression/
patterns/datasets/LLM evidence), and [design/index.md](design/index.md)
(task scaffolds). Consumed per the ground rule: **borrow the encodings,
not the model; build the prompt design and the loop.**

## container / transport

| What | Role | License |
|---|---|---|
| **zip (.mxl precedent)** | `.mu` container | — (public format) |
| **JSON manifest** | rights/provenance/hashes, plaintext | — |

## score parsing / note arrays (IR tools)

| What | Role | License |
|---|---|---|
| **Partitura** (CPJKU) | IR schema reference (note arrays, beat maps); MEI/Humdrum option; match-file conventions. W1's MusicXML/MIDI parsers are direct, not Partitura — swap recorded in [design/w1-event-ir.md](design/w1-event-ir.md) | GPLv3 |
| **musicxml2hum / Verovio** (rism-digital) | optional debug engraving | — |
| **mido / midiutil** (spike/py) | MIDI event vocabulary (tools/ir MIDI parser + spike) | MIT/Apache |

## pattern discovery / analysis (W3/W6)

| What | Role | License |
|---|---|---|
| **Ostinato** (SIATEC/SIATEC-C) | maximal repeated pattern discovery | open |
| **RegularTimeInterval_Patterns_Discovery** (MathysDaniel) | rhythm/meter complement | open |
| **NCD metrics / Patterns UI** (SMC 2024) | evaluation + review | scholarly |

## score↔performance alignment (W4/L4)

| What | Role | License |
|---|---|---|
| **Parangonar** (sildater) | DTW note-alignment engine | open |
| **Parangonada** (sildater) | visual correction of alignments | open |
| **pyAMPACT** | audio↔symbolic descriptor linking | open |
| **match-file format** (Foscarin et al., MEC 2022) | alignment convention | documented convention |

## renderer tiers (P2, L2, L5 gate)

| What | Role | License |
|---|---|---|
| **sfizz** | SFZ/sample renderer | permissive |
| **FluidSynth** | baseline soundfont | LGPL |
| **VSCO2 CE** | sample library | CC0 |
| **VPO** | aggregated free library | mixed free |
| **Sonatina SSO** | sample library (spike used) | CC Sampling+ |
| **spirfire/Kontakt-class** | commercial tier (only if L5 waivers) | per contract |

## tokenization for prompts (C2/L1)

| What | Role | License |
|---|---|---|
| **MidiTok / REMI+** | prompt export shapes | Apache/MIT-family |
| **MusicBERT / OctupleMIDI** | compact per-note tokens | research |

## plot / report generation (W5)

| What | Role | License |
|---|---|---|
| **matplotlib** | piano-roll images | liberal |

## build — the things that are the product

- **W1 (IR)**, **W3 analyzer**, **W4 diff**, **W5 viz** — internal tools.
- **S specs** — the format itself (public at launch).
- **C workbench + L harness** — the proprietary products.
- **E event** — the staged unveiling.

## not used (deliberately)

- ACCompanion, VirtuosoNet — too model-dependent; we build the harness.
- ASMD — a framework, not a corpus; used as a download/interface layer.
- Text2midi, ComposerX, ChatMusician, MuseCoco — pattern sources for
  prompt design, not runtime deps.

Sources: [prior-art-spike.md](prior-art-spike.md),
[literature-review-w1.md](literature-review-w1.md) §6, delta sources per
[delta-analysis-plan.md](delta-analysis-plan.md).
