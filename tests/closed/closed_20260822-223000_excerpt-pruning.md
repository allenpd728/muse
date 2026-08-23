# Test spec (closed): --bars excerpt pruning (issue #120)

**Coverage landed in `tests/play-excerpt.test.mjs`** (11 pins, offline —
no live calls), run via `npm test`:

- Unit pins on `tools/excerpt.mjs`: order prefix truncation, repetition
  clamped to kept occurrences (`--bars 12` → `{verse.1:{1,1}}`), fully-kept
  sections keep original bounds (`--bars 36` → `{2,4}`), dropped-section
  tempo_shapes pruned, global constraints (tempo_lock/register/must_contain)
  preserved, source document not mutated.
- Winnability pin: `scorePerformance(excerptDoc(full,12), expandOffline(...))`
  → structure_fidelity === 1, tempo_shapes === 1 (no dangling obligations —
  the unwinnable-by-construction failure mode from #113).
- CLI pin: `node tools/play.mjs examples/full.muse.json r.synthwave --bars 12`
  exits 0 through the refs/semantics guard seam; perf + WAV written.

Live confirmation (manual, closing comment on #120): gemini-3.6-flash
expanded the previously-unwinnable excerpt in 2 attempts; all four
conformance metrics 1.0.
