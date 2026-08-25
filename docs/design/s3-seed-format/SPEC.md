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
  { region: [onset_start, onset_end], kind: ornament, budget: 0.2, assertions: {..} }
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
- **Variation points (S3.4, 2026-08-23):** frozen schema
  `{region: [start_tick, end_tick], kind, budget: 0..1 (default 0.2),
  assertions: {}, label?}`. Regions are IR ticks (half-open
  `[start, end)`). Kind vocabulary: `ornament`, `repeat`, `cadenza`,
  `ossia`, `tempo_flex`. Regions must not overlap (adjacency is fine) and
  may be work-bounds-checked against `Work.duration_ticks()` when the work
  is loaded. Attached assertions are restricted to S3.5's kinds
  (`must_contain`, `register`, `form`, `tempo_bounds`) and are evaluated by
  `muse_assert` against a performance; the `assert` key from the draft
  renamed to `assertions` for grammar uniformity. Validator:
  `tools/muse_seed/variation.py`, wired into `validate_seed()`
  (`variation_points` key from S3.1).
- **Era budget (2026-08-24, #236):** optional top-level `era_budget` field.
  Authoring provenance, not interpretive space: the budget table that
  sanctioned the proposal's ranges, captured at authoring time so the
  proposal stays auditable when era budgets are recalibrated later (C3/C5).
  Mapping when present; absent on hand-authored seeds. C1
  (`muse_seed_cli validate`) requires it on proposals whose
  `provenance.author` is `muse_author`. Additive — no existing seed
  breaks; v0 grammar per §6.
- **Lineage fields (S3.7, 2026-08-25, #248):** two optional top-level
  `provenance` keys make a seed revision's authoring chain walkable.
  `extends` is the bare 64-hex SHA-256 (the exact digest shape
  `tools/muse_mu/manifest.py`'s `_validate_hashes` validates — no
  `sha256:` prefix) of the *parent artifact's committed file bytes*: a
  prior seed revision, or the mockup the revision was distilled from
  (L4). Omitted for a root seed. Committed bytes, not a canonical
  serialization — lineage points backward at immutable committed
  revisions, and editing a parent produces a new revision, which is
  exactly what the chain should detect. `operation` is the
  `tool@version` (lowercase tool dir name `@` digits, e.g.
  `muse_distill@1`) that produced the revision — informational only,
  never chain-verified. One hop over, the mockup schema's
  `provenance.seed_hash` (L1.10, #250) is the *same* hash: the value the
  mockup's seed carries as its identity and the next distilled revision
  puts in `extends`. Directive roots are out of scope until directives
  exist as files. Validator: `_validate_provenance()` in
  `tools/muse_seed/seed.py`, wired into `validate_seed()`. Additive — no
  existing seed breaks.
