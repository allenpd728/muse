# Spike round 2 — human-calibrated, era-informed (scoped)

**Purpose:** Test whether a mockup built with *human-measured* budgets and
the *universal chord-spread device* lands as "musical" to the founder — the
spike question, round 2, now that the vocabulary is empirically grounded.

**Material:** Byrd *Mass for Three Voices* — Kyrie (3 voices, ~2 min of
polyphony — more architecture than the chorale's 9 bars, small enough to
iterate). Source: `corpus/byrd/1-Kyrie.mid` (MIDI, no MusicXML — fine; the
spike needs notes only).

## What round 2 applies (from delta analysis, all four works)

**Delta findings ([mockup-delta-analysis.md](mockup-delta-analysis.md)):**

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
