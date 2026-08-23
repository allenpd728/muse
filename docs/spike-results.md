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
