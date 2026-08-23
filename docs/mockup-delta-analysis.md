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
