# Muse — Product Vision

## The idea

A Muse file is to a recording what a seed is to a tree, what a score is to a
performance: the compressed essence of a piece, expandable by any capable
intelligence. Sheet music already works this way — the same score produces
different music under different orchestras and conductors. Muse makes that
property computational: the `.muse.json` captures what makes the piece *this*
piece (themes, motifs, form, harmony, constraints), and leaves open what a
performer would decide (voicing, orchestration, microtiming, dynamics, timbre).
Interpreters differ; the work persists.

In compression terms: Muse is a lossy, non-deterministic protocol. Lossy on
purpose — the discarded information is where interpretive freedom lives.
Non-deterministic by design — the value of a file is the *space* of valid
performances, not one canonical output. The composer sets the compression ratio
per dimension: `globals` ranges loosen an axis, `constraints` tighten it.

## Components

1. **`.muse.json` schema** — the canonical artifact. Composition as a space of
   valid renditions. Spec: `SCHEMA_SPEC.md`.
2. **Performance layer** *(spec gap — to be authored)* — the concrete event
   format between interpretation and audio: expressive-MIDI-as-JSON. Note events
   with pitch/onset/duration/velocity/articulation, tempo and dynamics curves,
   instrument/patch assignments, mixing directives. Prior art to curate:
   Magenta NoteSequence (timing model), MIDI 2.0 (per-note controllers), MNX
   (JSON notation modeling). The interpreter writes it; the player reads it.
   This contract is the keystone of the product.
3. **Importer** — MIDI/MusicXML → `.muse.json`. Lossy: produces `material`,
   `globals`, a first-pass `form`, one default rendition; motif/role inference
   may be agent-assisted. Covers authoring until a composer tool exists.
4. **Interpreter** — any LLM, bring-your-own key. Expands `.muse.json` + an
   active rendition into a performance-layer document: resolves ranges,
   satisfies constraints, makes the expressive choices (the "humanizing" a film
   composer does when programming a mockup). The validator closes the loop:
   generate → validate → fix.
5. **Player** — deterministic, no AI required.
   - **V1:** synthesis + sample libraries. Target quality: the DAW mockup —
     Spitfire/Kontakt-class playback from expressive data. Fully owned, zero
     model dependency, free to run.
   - **V2:** optional audio-model plugins (`extensions.<namespace>`) for
     timbral realism as open audio models mature. Swappable, never a landlord.
6. **Composer tool** — node-based schema editor. Deferred; importer +
   agent-assisted authoring covers early needs.

## Users

- **Composer** — authors `.muse.json` (importer + AI assistance now, composer
  tool later). Releases the schema, not audio.
- **Listener / player user** — opens a file, picks a rendition preset, picks a
  model (own API key or local), hears the piece. Same file + different model =
  a different performance. That demo is the product.
- **Benchmark user** — feeds canonical files to multiple models and compares.

## Strategy

- **Own the format, not the models.** Licensing a frontier model is death by
  terms-of-service; training one is a capital war fought as a worse Suno. The
  interpreter is already commoditized (any LLM writes structured JSON); V1
  playback needs no model at all; every open audio-model release is a free
  upgrade to V2. Models compete; the format collects the rent.
- **The MIDI play.** MIDI won because it made keyboards and synths
  interchangeable and forced competition on sound. Muse is the neutral layer
  that makes music models interchangeable — and forces competition on
  interpretation quality. Adoption comes from user-side pull (free player,
  canonical corpus), not vendor goodwill.
- **The benchmark is the scoreboard.** A canonical corpus (public-domain
  scores — Bach chorales up to Beethoven's Ninth — imported to `.muse.json`)
  plus conformance metrics (motif recall, structure fidelity) makes model
  quality legible. Reference recordings are the yardstick models are measured
  *against each other by*, not a cloning target. Closed tools (Suno et al.)
  are benchmark opponents: probe what survives their genre transfers to learn
  what the format must encode.

## Explicitly not

- Recording → `.muse.json` → identical recording. Audio→symbolic transcription
  at orchestral density is unsolved research, and "nearly identical" is a
  marketing trap that demos our weakest links. **Lane 3 research watch:** if
  open audio→symbolic transcription matures, `.muse.json` is its natural
  output format. Until then, recordings are benchmark references, not inputs.
- A sealed model + subscription. That is the thing being replaced.

## Roadmap

```
Batch 1  Schema tooling: JSON Schema, validator, examples, CI
Batch 2  Importer: MIDI/MusicXML → .muse.json
Batch 3  Performance-layer spec → interpreter → Player V1
Later    Player V2 plugins, benchmark corpus + conformance harness
Watch    Open audio→symbolic transcription (unlocks Lane 3)
```

Feasibility note: expressive performance rendering is an established research
field (Magenta Performance RNN onward). Score → expressive performance is
tractable; Muse does it with a general LLM writing validated JSON instead of a
bespoke model.
