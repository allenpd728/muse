# Test spec — R2 rehearsal pane (implementation-facing)

Written 2026-08-26 per R1 (#282) §What R2 builds; spec for the tests R2
(#283) must land. R1 itself is document work and ships no runtime tests.

## Coverage R2 must write

Target: `tools/muse_rehearse/` (new) tests + a qa_frontend pane test,
run with `cd tools && python -m pytest muse_rehearse -q` and the
qa_frontend suite.

1. **Grammar accept/reject matrix.** Each of the five verbs
   (`rebalance`, `phrase`, `tempo_arch`, `rubato`, `hold`) parses a
   canonical example and compiles to the documented seed-knob effect
   (R1 §grammar table). Rejects: unknown verb, two verbs in one
   directive, unresolvable region reference, a part the work doesn't
   have — each with the valid-vocabulary error message.
2. **Region resolution.** A variation-point label resolves to its
   seed's tick region; a raw tick range passes through; a bar-style
   reference ("bar 40") is a parse error in v1 (R1 non-goal — pin it so
   a future IR bar-index deliberately flips this test).
3. **Dry-run = param_diff, no mockup.** The preview is computed
   seed-to-seed via `probe_param_diff` (R1 §dry-run UX); assert the
   compiler's candidate revision produces the expected param diff
   against the base seed and that no mockup is generated in the dry-run
   path (the stand-in stays out of the loop).
4. **Lineage-root semantics.** Committing a directive writes
   `seeds/<work>.directives/<slug>.directive.txt` and a candidate seed
   revision whose `extends` is the SHA-256 of the directive file's
   bytes; `muse_lineage.store_files` picks up `*.directive.txt`; the
   walk resolves revision → directive (root). The directive file itself
   has no `extends` (it IS the root — pin that the walker reports
   `root`, not `missing`).
5. **Budget clamping.** A directive whose degree exceeds the era budget
   clamps to the budget (not an error); the clamp is visible in the
   dry-run preview.
6. **Pane (qa_frontend, source-scan tier per current convention).** The
   Study/Rehearse pane exists in the workbench detail page, is
   half-width in the two-column `.panel` grid, contains the textarea +
   dry-run + commit/discard affordances, and carries no mockup JSON
   (D20).
7. **No auto-commit.** The dry-run path writes nothing (assert the
   store dir is unchanged after a dry run); only the explicit commit
   writes files.

## Known gaps (acceptable at R2)

- The pane's commit writes seed revisions; whether those revisions
  *perform better* is R3's feedback loop, not R2's test.
- Parse robustness beyond the verb+operand grammar (true NL
  understanding) is an R-series-later, typed-provider-gated feature.
