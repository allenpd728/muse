# Spike — the mockup proof

**Purpose:** Answer the existential question before building the harness:
*can an LLM do session work worth hearing?* If the LLM's mockup of a known
score sounds mechanical, the architecture needs rethinking at the cheap
stage. If it sounds musical, L1/L2 become engineering, not research.

**Cost:** one session, no new repo infrastructure. Everything hand-driven.

## Protocol

1. **Source:** one Bach chorale movement from `corpus/bach/` (MusicXML).
   The founder knows this repertoire — his ear is the evaluation.
2. **Parse:** extract the first phrase (~8 bars) to a minimal IR dump
   (hand-rolled for the spike; W1's parser formalizes it later).
3. **Hand-write a minimal seed:** tempo range, one philosophy line
   ("sing the chorale, breathe at phrase ends"), one assertion
   (all notes from the score present, order preserved).
4. **LLM session work:** an LLM produces a mockup JSON for the phrase —
   tempo map, dynamic curve, per-note velocity/duration offsets
   (humanization), articulation marks. Chunked if needed.
5. **Validate:** the mockup satisfies the assertion (score fidelity) —
   hand-checked for the spike; W4's diff tool automates it later.
6. **Render:** mockup JSON → MIDI → FluidSynth/sfizz → WAV.
7. **Evaluate:** the founder listens. Two questions:
   - Is it *musical* (phrasing, breathing, shape) or mechanical?
   - Could you tell it apart from a straight MIDI realization?

## Decision rule

- **Pass:** the mockup is distinguishable from mechanical playback, in a
  direction the founder calls musical. → Proceed to S-series; L1/L2 are
  engineering.
- **Fail:** indistinguishable from mechanical, or musical in a wrong
  direction. → Rethink the LLM's role (more structure in the seed?
  different mockup format? human-loop tighter?) before any harness work.

## What the spike is NOT

- Not a quality bar for the final product (sample tier, full seed, whole
  work — all later).
- Not a conformance test (nothing is pinned yet).
- Not automated (W-series tools formalize everything the spike hand-rolls).

## Record

Results, the mockup JSON, the WAV, and the founder's verdict land in
results section below.

---

# Spike round 2 — human-calibrated, era-informed (scoped)

**Purpose:** Test whether a mockup built with *human-measured* budgets and
the *universal chord-spread device* lands as "musical" to the founder — the
spike question, round 2, now that the vocabulary is empirically grounded.

**Material:** Byrd *Mass for Three Voices* — Kyrie (3 voices, ~2 min of
polyphony — more architecture than the chorale's 9 bars, small enough to
iterate). Source: `corpus/byrd/1-Kyrie.mid` (MIDI, no MusicXML — fine; the
spike needs notes only).

## What round 2 applies (from delta analysis, all four works)

**Delta findings ([delta-analysis-plan.md](delta-analysis-plan.md)):**

| Era | Duration spread | Velocity spread | Chord spread |
|---|---|---|---|
| Mozart (Classical) | 75% | 18% | 17ms |
| Chopin op.10 no.3 (Romantic) | 36% | 145% | 16ms |
| Schubert (early Romantic) | 64% | 16% | 16ms |
| Chopin op.38 (Romantic) | 31% | 195% | 17ms |

**The convention signature:** Classical-era freedom lives in tempo;
Romantic-era freedom lives in dynamics; chord spread (~16–17ms melody-lead)
is the universal device across eras.

## The mockup v3 (to be authored, not auto-generated)

For the Byrd motet (Renaissance → Classical-lean budget):

- **Tempo envelope:** wide (Classical-style ±35% budget), breathing at
  cadences, ritardando into each section's close
- **Chord spread:** 15–18ms melody-lead on chordal arrivals — the missing
  device, now included
- **Voice entries shaped:** imitative entries (soprano → alto → bass)
  treated as events: slight anticipation on the answering voice, gentle
  decrescendo into stretto
- **Dynamics:** consort-like contour, phrase-end releases (human vel std
  ~15 within performance)

## Renders to compare on the listener

- **A3 — Mechanical** (Byrd, straight)
- **B4 — Mockup v3** (Byrd, human-calibrated)
- (For reference: chorale B2/B3 remain on the page)

## Decision rule (same as round 1)

Pass if the Byrd mockup is *clearly* more musical than mechanical, beyond
the chorale's marginal verdict. Fail → the sample ceiling hypothesis
(hypothesis 2 from the checkpoint) gains, and the event tier needs
commercial libraries; the LLM vocabulary is not the blocker.

## Out of scope

- No new renderer work (same spike-grade SSO renderer)
- No new delta analysis (per-phrase curves deferred to W-series)
- One work, one mockup, one verdict — then the spike closes and Phase 3
  (seed authoring) starts properly

---

# Spike results — verdict and lessons

**Date:** 2026-08-23. **Verdict: CONDITIONAL PASS.** The pipeline works; the
interpretation is musical but not yet compelling. The spike closes here;
what it taught us drives Phase 3 design.

## What was tested

Two works, three mockup versions, two renderer tiers — all artifacts in
[spike/](spike/) with the listener page.

| Round | Material | Mockup | Renderer | Verdict |
|---|---|---|---|---|
| A1/B1 | Bach chorale, 9 bars | v1 (phrase-level) | GM choir | "slight difference, not apparent" — GM masks interpretation |
| A2/B2 | Bach chorale | v1 | SSO strings | "slightly more musical nuance" — per-note layer missing |
| A2/B3 | Bach chorale | v2 (per-note sculpting) | SSO strings | "very lightly more musical" — interpretation too timid |
| A3/B4 | Byrd Kyrie, 3 voices | v3 (human-calibrated budgets) | SSO strings | "better, pleasant, not overly expressive — good enough for now" |

## What the spike proved

1. **The pipeline works end to end.** Score → mockup → render → listen, all
   functioning, all committed.
2. **The mockup vocabulary exists and matters.** Per-note sculpting (attack,
   release, swell, timing) is audible; the delta analysis grounded the
   budgets empirically.
3. **Renderer quality gates audibility.** GM masked everything; SSO strings
   made interpretation perceptible. Tiers are not optional.
4. **The seed's role is real.** Expression budgets (v3) are the permission
   layer — the composer/encoder's control over how much sculpting is
   sanctioned.

## What the spike did NOT prove

1. **Compelling interpretation.** "Not overly expressive" is the honest
   ceiling so far. The mockups were hand-written sketches (dozens of
   touched notes), not full-density session work. The DNA-density gap: a
   real mockup touches **every note**; the spike touched ~15 of 71.
2. **The sample ceiling.** SSO sustains have no true legato; the singing
   between notes is what free samples lack. Event tier may need commercial
   libraries (budget decision, deferred).
3. **LLM boldness.** My mockups were conservative. Whether a stock LLM
   produces a *bold* reading when the seed permits it is unproven — that's
   the Phase 3 question.

## Lessons for Phase 3 (seed authoring)

- **The mockup is dense data, not a sketch.** Design the format for full
  DNA density — every note sculpted — not hand-inspectable JSON.
- **The seed carries the intelligence.** Budgets, philosophy, sanctioned
  space — the LLM's job is to fill the space boldly, the seed's job is to
  make boldness safe.
- **Material matters.** Chorales give interpretation nothing to grab;
  polyphony and dramatic works do. Corpus ladder order is correct.
- **Match samples to material.** Strings on vocal polyphony sounded
  "choral" by register coincidence; the Byrd needs consort viols or voices.

## Decision

Proceed to Phase 3 (seed authoring) scoping. The spike's conditional pass
means: the architecture is sound, the vocabulary is proven, the craft of
interpretation is the work ahead.
