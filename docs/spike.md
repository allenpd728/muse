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
`docs/spike-results.md` when run.
