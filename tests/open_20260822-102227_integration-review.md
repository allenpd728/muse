# Test spec: convention lint (from #37 cross-schema integration review)

Task: #37 (Batch 1 cross-schema integration review). The review verified these
conventions by hand; this spec codifies them so Batch 2+ schema work can't
re-introduce drift silently. File as `tests/conventions.test.mjs`, folded into
`npm test` via the harness's `tests/*.test.mjs` pickup.

Note: some assertions encode the *resolved* form of corrective tasks #43–#47.
Where a corrective task is still open, the corresponding assertion should test
the current convention (e.g. transform grammar enforced at both ref sites only
after #46 lands) — or the test issue should be worked after the corrective
tasks. The harness already proves the happy path; this suite guards the
invariants.

## Behaviors to verify

1. **Naming**: every property name in every `schema/*.schema.json`
   (`properties` keys, recursively) is snake_case: `^[a-z][a-z0-9_]*$`.
   Exception: none expected today; fail loudly so a new one is a conscious
   choice.
2. **Sealed objects**: every fixed-shape object schema (an object with
   `properties` that is not a documented map) carries
   `additionalProperties: false`. Documented exceptions (assert these stay
   open instead): `form.repetition`, `constraints.tempo_lock`,
   `constraints.register` (map-valued), `constraints.must_not` predicates,
   `extensions` (`true`). After #45 lands, `metadata.provenance` items must be
   sealed — that assertion is the regression guard for #45.
3. **Id grammar** (after #43): `metadata.id` validates against the agreed
   pattern, and the spec example's form is a passing case, not just a rejected
   one — spec and schema must accept the same documents.
4. **Pitch grammar** (after #44): `material.motifs[].pitches` and
   `constraints.register` bounds reject non-pitch strings (`"banana"`,
   `"42"`, empty) and accept the example's pitches (`D4`, `A5`). One shared
   `$defs` entry referenced from both schemas (assert by schema inspection,
   not just behavior).
5. **Transform refs** (after #46): `form.sections[].uses[].ref` rejects
   malformed transform suffixes (`theme.1###`, `theme.1#unknown`) exactly as
   `themes[].phrases[].motifs[]` does; both accept `id#seq(+2)`, `#inv`,
   `#retro`, `#aug(2)`, `#dim(0.5)`.
6. **Cross-ref coverage** (after #47): `danglingRefs()` from `tools/test.mjs`
   flags a ghost id in each of: `themes[].phrases[].motifs[]`, `form.order`,
   `form.repetition` key, `constraints.tempo_lock` key,
   `constraints.register` key — one assertion per surface, using
   `examples/full.muse.json` clones with one id mutated.
7. **Seam exercise**: `examples/full.muse.json` continues to reference at
   least one motif with a transform suffix inside a theme that is used by a
   section that is named in `constraints.tempo_lock` — the review's
   cross-seam thread, asserted so future example edits don't quietly sever
   it.

## Invocation

`npm test` (harness picks up `tests/conventions.test.mjs` automatically);
standalone: `node tests/conventions.test.mjs`.
