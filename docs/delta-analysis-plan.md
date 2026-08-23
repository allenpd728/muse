# Naming check + the delta-analysis data problem (2026-08-23)

Two findings from the field, both affecting next steps.

## 1. Naming: `.mu` and "Muse" both collide

- **`.mu`** — taken by Kerbal Space Program's model format (proprietary 3D
  mesh) and by the `mu` Lisp dialect toolchain (scripts/bytecode). Neither is
  music-adjacent, but both are real.
- **"Muse"** — saturated: Muse Group / MuseScore (the notation company whose
  file ecosystem we'd interoperate with — worst possible confusion), the band.

Options when naming matters (at public launch, not now):
- Keep the project name, change the extension: `.muse` (unused by anything
  significant), `.muw` (muse work), `.egg` (on-metaphor, memorable, probably
  too cute).
- Rebrand entirely — deferred; "muse" works fine as an internal codename.

**Decision for now:** keep writing `.mu` in docs (it's short), flag the
extension as an open question at launch. No urgency — nothing is public.

## 2. The delta-analysis data problem

The subtraction method needs (work × raw score × artistic session) triples.
Field findings:

- **Producers don't publish DAW sessions.** Sessions are private craft;
  film-score templates are discussed endlessly, shared never. The
  DAWproject repo itself ships zero example sessions (schema + one wav).
- **What researchers publish instead is better for our purposes:**
  score↔performance *alignment* datasets — real conductors' recordings
  aligned note-by-note to the score:

| Dataset | Contents | Eras | Access |
|---|---|---|---|
| **Vienna 4x22** (Cancino-Chacón et al., JKU) | 4 Mozart piano sonatas × 22 skilled performances each, note-level aligned | Classical | Open (CPJKU) |
| **Batik / Magaloff** datasets | Chopin (Batik: ~50 performances; Magaloff: complete opp. 10/25, aligned) | Romantic | Open (JKU/MDW) |
| **Bach chorales corpora** (various) | Multiple performances, aligned | Baroque | Open |
| **BSED** (T-ISMIR 2025) | Beethoven symphony excerpts, score-aligned orchestral recordings | Classical/orchestral | Zenodo, open |
| **Nakamura et al. alignments** | Mozart/Beethoven piano works, aligned | Classical | Open |

**This is the delta corpus.** A conductor's aligned performance minus the
score IS the interpretive delta — the same subtraction, measured on *real
artistic interpretations* instead of DAW sessions. And the JKU tooling we
already flagged (Partitura, Parangonada, Basis Mixer) is built to compute
exactly these deltas.

**Era coverage for the producer-convention analysis** (baroque vs classical
vs romantic interpretation conventions):
- Baroque: Bach chorale corpora
- Classical: Vienna 4x22 (Mozart), Nakamura (Beethoven), BSED (orchestral)
- Romantic: Batik/Magaloff (Chopin)
- Film-score flavors: derivative of the above — film scoring *applies* these
  conventions per cue; no separate corpus needed for v0.

**Plan adjustment:** the subtraction method runs on score↔performance
alignment datasets, not DAW sessions. First analysis target: Vienna 4x22 —
22 pianists playing the same Mozart phrase gives 22 measured deltas of the
same material: the empirical distribution of interpretation conventions.
Output: this document — which expressive parameters vary,
by how much, and which are era-typical. That becomes the mockup schema's
ground truth and the seed's budget calibration.

DAW sessions remain a nice-to-have (a producer collaborator donating one
would be gold), but they are no longer the plan.

---

# Mockup delta analysis — Vienna 4x22, first results

**Date:** 2026-08-23. **Dataset:** [OFAI/vienna4x22_rematched](https://github.com/OFAI/vienna4x22_rematched)
(CC-BY 4.0; original corpus: Goebl 1999, Bösendorfer SE290 computer grand).
**Script:** [tools/spike/delta_analysis.py](../tools/spike/delta_analysis.py).

The subtraction method, first measurement: 22 skilled pianists × the same
18 bars (Mozart K.331, 1st movement, bars 1–18). Performance minus score =
the interpretive delta, in numbers.

## Measured deltas

| Dimension | Human range across 22 pianists | Design implication |
|---|---|---|
| **Total duration** | 86.6s – 151.4s — **75% spread** | Tempo freedom is massive. The spike's ±15% mockup tempo range was timid by 5×. Seed tempo budgets must allow for radically different readings (this is the Furtwängler-vs-Toscanini range, measured). |
| **Mean velocity** | 86–101 — 18% spread | Overall loudness persona varies modestly. Velocity *range within* a performance (std 11–21) matters more than the mean. |
| **Chord spread** (melody lead / arpeggiation) | mean **17ms**, range 14–18ms | **Universal device, absent from spike mockups.** Every pianist breaks chords slightly, melody first. Must enter the mockup vocabulary as a per-note onset device and the seed as a sanctioned parameter. |
| **IOI coefficient of variation** | mean 1.46 | Timing freedom within a performance is high; beat-level microtiming is the norm, not the exception. |

## What this settles

1. **The mockup vocabulary needs chord spread** (per-note onset offsets
   ordered by voice/melody priority) as a first-class device — it is the
   single most consistent human behavior in the dataset.
2. **Seed budgets calibrated from humans, not guesses:** tempo range must
   span at least ±35% around nominal (the observed 75% total spread across
   readings); onset offsets in the tens of ms, not single ticks.
3. **The spike's "lightly more musical" verdict is explained:** the spike
   mockup used ~1/5 of the human tempo envelope and lacked the one device
   (17ms spread) every human uses.

## Era comparison (all four works)

| Work (era) | Duration spread | Velocity spread | Chord spread |
|---|---|---|---|
| Mozart K.331 (Classical) | **75%** | 18% | 17ms |
| Chopin op.10 no.3 (Romantic) | 36% | **145%** | 16ms |
| Schubert D.783 (early Romantic) | 64% | 16% | 16ms |
| Chopin Ballade op.38 (Romantic) | 31% | **195%** | 17ms |

**The convention signature:** Classical-era freedom lives in *tempo*;
Romantic-era freedom lives in *dynamics*; chord spread (~16–17ms melody-lead)
is the universal constant across eras. Seed budgets are era-calibrated
parameters, not global constants — exactly the producer-convention question,
answered with data.

## Method notes

- MIDI files converted tick→seconds honoring each file's tempo map
  (`tools/spike/delta_analysis.py`).
- Chord spread: max−min onset within 30ms simultaneity windows.
- This is the *summary* level; per-phrase delta curves (where in the form
  the freedom concentrates — cadences, phrase ends) are the next analysis,
  and they map directly to seed variation points.

## Next

- Per-phrase delta curves (where do pianists spend their freedom?)
- Same analysis on Chopin op.10 no.3 (Romantic contrast — expect bigger
  spreads) and Schubert D.783
- Then: mockup v3 with chord spread + human-calibrated budgets on the
  chorale, rendered and posted to the listener for verdict.
