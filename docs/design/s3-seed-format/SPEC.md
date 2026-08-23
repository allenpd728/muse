# S3 — Seed format (spec v0 draft)

**Status: draft.** The prompt: sanctioned parameter ranges, performance
philosophy, variation points, and assertions. Calibrated from
[delta-analysis](../delta-analysis-plan.md) evidence. Human-authored or
human-approved; never machine-invented without review.

## 0. Domain

A **seed** is the interpretive space of a `.mu` work. It does not perform;
it permisses and biases. Bounded by assertions.

## 1. Parameters with ranges

Typed ranges over the W1 IR:

```yaml
tempo:        { min_bpm: int, max_bpm: int, default_bpm: int }
energy:       { level: 0..1, shape: curve_ref }
density:      { notes_per_beat: [min, max] }
variation:    { level: 0..N, points: [section_ref, ...] }
```

Sources of calibration: Vienna 4x22 (total-duration spread ~75% over the
same 18 bars) → tempo budgets at least ±35%. Velocity budgets via
Magaloff (Romantic spreads ~145–195%). Chord spread ~16–17ms universal.

## 2. Philosophy declarations

Free-text or typed philosophy fields, referencing styles/eras/practices not
artist identities without license:

```yaml
tempo_philosophy:    "flexible, architectural"
dynamic_philosophy:  "terraced, dramatic"
articulation_stance: "consort, breathe at cadences"
```

## 3. Variation points

Named regions with bounds (ornamentation zones, optional repeats,
cadenza-like freedom); each with assertions attached:

```yaml
variation_points: [
  { region: [onset_start, onset_end], kind: ornament, budget: 0.2, assert: [..] }
]
```

## 4. Assertions

Every performance validates against invariants (fail loudly, never silently
deviate):

```yaml
must_contain: [theme_ref(...)]
register:     { part: "celli", min: "C2", max: "C4" }
form:         { sections: [A, B, A], repeats: [..] }
```

## 5. Validation

Any performance (mockup/event stream) must satisfy the seed. A validator
library consumes (seed, mockup, diff) → pass/fail. This is exactly C1's
implementation surface.

## 6. Schema shape (v0 grammar)

YAMLClass of a strict subset, tokenized later by MidiTok for C2/L1 prompt
use. Byte-exact for serialization depends on C1.

## Open questions

- Whether `philosophy` is typed-enum-lite or free-text (typed-lite first:
  known values + free-text escape).
- How vocal/choral text rides seeds (defers to S6's schema sub-task).
- YAML vs JSON for seeds (YAML for author-editability; JSON for machines).

## Decisions log

- **Philosophy (S3.3, 2026-08-23):** typed-lite, as drafted. Closed field set
  (`tempo_philosophy`, `dynamic_philosophy`, `articulation_stance`,
  `ornamentation_stance`, `ensemble_stance`); values are list entries, each
  either a vocabulary term (additive-only: new terms may be added, existing
  ones never removed) or free-text (the sanctioned escape). Identity guard:
  any capitalized name-like phrase is a suspected artist identity and
  requires `provenance.license_ref`; era phrases ("Viennese Classical",
  "Venetian School") are whitelisted as styles, not identities. Provenance
  per philosophy block: `author` (required) and `ai_assisted` (required
  boolean — the manifest's AI-disclosure rule applied at seed granularity).
  Validator: `tools/muse_seed/philosophy.py`, wired into
  `validate_seed()` (S3.1's surface).
