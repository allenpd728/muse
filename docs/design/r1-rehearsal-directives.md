# R1 — Rehearsal directives: typed natural-language→seed revision grammar

**Status: design doc (R-series root). Task #282.** Defines the rehearsal
directive grammar, the dry-run UX, the lineage-root semantics, and the
format-first review bounding what directives may express. No
implementation here — R2 builds the pane, R3 the training layer.

A rehearsal directive is how the conductor talks to the ensemble in
words — *"bring the horns up at bar 40," "quieter pickup into mvt 2"*
— typed into the workbench, compiled to a seed revision on dry-run, and
committed (or discarded) after the conductor sees the computed delta.
The feature exists because the seed knobs are correct but illegible: the
conductor's intent lives in natural language, and the revision should
say *why* it exists, not just *what* changed.

## Lineage-root semantics

The lineage chain (`docs/design/proposal-lineage-chain.md` §1) sketched
this and deferred it: *directive → seed → mockup → revised seed*, with
the directive as the chain root. R1 makes that real.

- **A directive is a committed text artifact.** Path convention:
  `seeds/<work>.directives/<slug>.directive.txt` (a directory beside the
  seed revisions, because one work accumulates many directives). Plain
  text, first line is the directive sentence; anything after a blank
  line is free-form conductor notes (not parsed).
- **The directive is the root; its hash is the seed's parent.** When a
  directive compiles to a seed revision, that revision's
  `provenance.extends` is the bare 64-hex SHA-256 of the *directive
  file's committed bytes* — the same S3.7 convention as mockups. The
  walk then reads: revised seed → directive (root). This resolves the
  proposal's §1 "Directive root: deferred" note with the mechanism it
  anticipated: directives are now files.
- **The store scan already finds them.** `muse_lineage.store_files`
  globs `*.seed.yaml` / `*.mockup.json`; R2 adds `*.directive.txt` to
  the store patterns (one-line change, noted here so the format is
  decided with the grammar, not patched in later). The walker reads
  provenance structurally, so a directive file needs no `extends` of its
  own — it *is* the root by construction.
- **Why root and not a mockup-parent:** a directive is human-authored
  intent, upstream of any seed. It has no parent. This is the third
  root type the chain supports (alongside root seeds and, one day,
  work-level scores), and the first that is pure text.

## The grammar

Directives are *typed natural language*: a leading verb-token selects a
compiler rule; the rest of the sentence is parsed for operands (target
part, region, degree). Free-text without a recognized verb-token is a
parse error, not a silent no-op — the dry-run preview is where the
conductor learns the vocabulary.

The format-first rule (below) fixes the verb set to what the seed can
already express. **Five verbs ship; nothing else.**

| Verb | Operands parsed | Seed-knob effect (the compiled delta) |
|---|---|---|
| `rebalance` | target part(s), direction (`up`/`down`/`quieter`/`louder`/`bring … up`), region (tick range or variation-point label) | energy/balance shaping for the named part(s) in the region: a part-scoped energy delta, clamped to the era budget |
| `phrase` | direction (`quieter`/`broader`/`lean-in`/`back-off`), boundary/region ref (a variation-point label, or a tick range) | a `variation_points` entry with `kind: tempo_flex` + an energy dip or arch at the boundary; region resolved to ticks |
| `tempo_arch` | shape direction (`wider`/`narrower`/`settle`), optional degree | `params.tempo` bounds widened/narrowed within the era budget (`tempo_budget(era)`) — see the note below on why it does *not* touch philosophy |
| `rubato` | degree (`more`/`less`/numeric), region (default whole work) | rubato/onset-offset budget within the era `chord_spread_ms` calibration; surfaces as a distiller `rubato_pstdev_ms` target |
| `hold` | region ref | an assertion (`tempo_bounds`) pinned narrower than the current budget for the region — the "do not move here" directive |

### Why these five

Each verb maps to an *existing* seed knob with an existing validator and
an existing delta measurement (W3/delta vocabulary: tempo, velocity,
IOI/onset-offset, balance). The grammar is a compiler from conductor
language to knobs — it invents **no new format semantics**. That is the
entire format-first review, made concrete in the next section.


> **`tempo_arch` compiles to tempo bounds, not the philosophy field.** The
> tempo *shape* vocabulary ("arch", "terraced") lives in
> `tempo_philosophy`, which is a philosophy field � and philosophy edits
> are authoring, not rehearsal (see the rejected list). A rehearsal
> directive can only move the *parametric* knob: how wide the tempo may
> swing. If a conductor wants to *change the philosophy itself*, that's a
> seed edit through C2 authoring, not a directive. This is the
> format-first rule cutting the other way: it stops the grammar from
> silently conflating two different kinds of change, which is exactly
> the conflation that would make R3's "did it survive the render"
> unmeasurable.

### Parse rules (deliberately small)

- One verb per directive. A directive with two verbs ("rebalance and
  tempo_arch") is a parse error suggesting two directives — the lineage
  model wants one intent per root.
- **Region references are tick-based.** The W1 IR model does not carry
  measure/bar structure (notes are tick-positioned; barlines are not
  surfaced), so a directive names its region as ticks or as a
  *variation-point label/section reference the seed already defines*
  (S3.4 variation points have optional `label`s and tick `region`s —
  reuse that vocabulary rather than inventing a bar-map). A "bar 40"
  style reference is therefore **not** in the v1 grammar; it needs an
  IR bar-index (a W-series addition), and is listed under non-goals so
  the grammar doesn't promise a resolution the IR can't give. An
  unresolvable region reference is a parse error, not a guess.
- Degrees default to the era budget's midpoint when unquantified; the
  dry-run preview shows the actual number so "bring the horns up"
  becomes "+8% energy in the named region" before it commits.
- Unknown verb, unresolvable region, or a part the work doesn't have →
  a parse error listing the valid verbs/regions/parts. The dry-run is
  the teacher.

## Dry-run UX (R → delta preview → commit)

```
directive text
     │  parse → compile → candidate seed revision (in memory)
     ▼
delta preview: param diff vs the base seed (the W-B1 param_diff probe,
     computed seed-to-seed — no mockup needed, so it's fast)
     │  conductor reads "what this actually changes"
     ▼
commit  → write directive file + candidate revision, stamp
          extends: sha256(directive bytes), operation: muse_rehearse@1
discard → nothing written; the loop is free
```

The preview is the rehearsal: the conductor sees the compiled delta
*before* anything is committed, so the cost of trying an idea is zero
and the committed chain only contains directives that survived review.
This mirrors the growth harness's "compare deltas, never auto-apply"
rule (L4 stays human-reviewed) applied to authoring.

## W-B pane layouts

New pane in the workbench detail page, half-width (the `.panel` grid is
already two-column; the pane is a full-row card split internally):

- **Study pane** (left half): the committed directive history for the
  work — one row per directive file (slug, first line, the revision it
  produced, whether its lineage verifies). This is the rehearsal log.
- **Rehearse pane** (right half): directive textarea → [Dry run] →
  delta-preview table (same row format as the probe panel's param diff)
  → [Commit] / [Discard]. Commit is wired to the seed-revision flow
  (writes both files, re-stamps lineage, regenerates the probe artifact).

The pane reuses existing surfaces rather than inventing new ones: the
param-diff probe for the preview, the seed-revision write path for
commit, the lineage walker for the Study pane's verify column.

## Format-first review (the gate)

The rule from AGENTS.md: *if a behavior can't be expressed in the spec,
amend the spec — never hard-code it into a tool.* Applied to directives:

**Allowed (ship in the five verbs):**
- chords/balance → `rebalance` (energy/balance is a seed knob)
- phrasing → `phrase` (tempo_flex variation + energy shaping)
- tempo architecture → `tempo_arch` (energy.shape + tempo bounds)
- rubato → `rubato` (onset-offset budget, delta-measured)
- regional constraint → `hold` (assertions, already sanctioned)

**Rejected (would invent format semantics — out of the grammar):**
- **Orchestration/timbre** ("make it brassier") — no seed knob for
  instrumentation; that's the score/renderer's domain, not the prompt's.
- **Articulation text** ("more staccato") — articulation stance is a
  philosophy *field*, not a parametric knob; a directive can't calibrate
  it, and pretending it can is exactly the silent-no-op failure the
  dry-run exists to prevent. (A philosophy *edit* is a seed edit, not a
  rehearsal directive.)
- **Note-level edits** ("fix the wrong note in bar 3") — directives act
  on the interpretive space, never the score. D1: the score is fixed.
- **Any verb the delta vocabulary can't measure** — if we can't tell
  whether the directive survived the render (R3's feedback loop), it
  doesn't belong in the grammar.

New verbs are added the way the spec grows: amend the seed format with
the knob first (S-series), *then* add the verb that compiles to it.
Grammar never leads format.

## What R2 builds (the contract this doc sets)

1. Directive parser + compiler per the grammar above (a
   `tools/muse_rehearse/` package, operation tag `muse_rehearse@1`).
2. The Study/Rehearse pane per the layout above.
3. Commit path: write directive file + candidate revision, stamp
   `extends: sha256(directive bytes)` + `operation`, regenerate probes.
4. `muse_lineage.store_files` += `*.directive.txt`.
5. Dry-run = the existing param_diff probe computed seed-to-seed (no
   mockup required — keeps the loop fast and the stand-in out of it).

## What R3 builds on top

Pre-composed directive *scripts* (study sequences — "quiet the cellos
into the development") plus the feedback loop that checks, per
committed directive, whether the compiled delta survived the render —
the distiller's `Interpretation` fields (`tempo_curve_shape`,
`velocity_pstdev`, `rubato_pstdev_ms`, `part_gains`) are exactly the
"did it survive" measurements, keyed by the verb that produced them.
That's how the conductor's ear gets trained without live musicians:
the system says whether the directive did what was asked.

## Explicit non-goals

- No LLM in the directive path. The grammar is a deterministic compiler;
  natural-language *understanding* beyond the verb+operand parse is a
  later, separately-reviewed feature (and would need the typed-provider
  contract, not this doc).
- No philosophy-field directives (see rejected list).
- No score edits. Ever.
- No auto-commit. Every committed directive passed a human's dry-run.
- **No bar/measure region references in v1.** The W1 IR doesn't surface
  bar structure; regions are tick ranges or variation-point labels. A
  bar-indexed reference syntax ("bar 40") wants a W-series IR bar-index
  first — format leads grammar, as with verbs.
