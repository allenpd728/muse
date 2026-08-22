# Test spec — #92: importer theme assembly + uses wiring

**Source task:** #92 (assemble themes + wire section.uses, heuristic marked)
**Code under test:** `importer/synthesize.mjs` (assembleThemes, uses wiring);
`benchmark/corpus/*.muse.json` regenerated.

DoD coverage landed with the task: `tests/synthesize.test.mjs` — 7 new
checks (assembly ≥1 theme, refs resolve, uses wired, inference marked,
schema-valid output, no-overlap fallback to bare pool, determinism);
corpus re-imports verified (all 10 entries ≥1 theme; sections with forms
carry uses; cross-ref lint green; corpus suite 46/46 incl. re-import
determinism). This spec is for what remains.

## Behaviors to verify

- **Overlap-tie policy:** two candidates with equal overlap — current
  tiebreak is longer motif first; pin the choice with a crafted IR where
  order matters.
- **Chain quality bounds:** assembly never produces a theme longer than
  the source phrase (chain motifs share seams; a pathological IR
  shouldn't chain indefinitely) — pin a sane cap or cycle guard.
- **uses-to-themes vs uses-to-pool mixing:** a doc where some sections
  have themes and others don't (multi-section imports when section
  detection improves) — wiring per-section.
- **Rendered output sanity:** corpus entries with themes now render via
  the uses path (not the #91 fallback) — pin that expandOffline picks
  theme phrases for bwv269 (uses present) and falls back only for
  section-less behavior.
- **Cleanup-agent ergonomics:** `extensions.importer.inferred` entries
  for themes/uses carry enough to undo the inference (theme ids listed?) —
  decide if the reason strings need the motif chain recorded.

## How to run

`npm test`; new cases into `tests/synthesize.test.mjs`.
