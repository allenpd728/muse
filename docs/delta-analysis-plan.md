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
Output: `docs/mockup-delta-analysis.md` — which expressive parameters vary,
by how much, and which are era-typical. That becomes the mockup schema's
ground truth and the seed's budget calibration.

DAW sessions remain a nice-to-have (a producer collaborator donating one
would be gold), but they are no longer the plan.
