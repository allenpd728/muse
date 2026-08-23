# Test spec — #71: benchmark corpus import set

**Source task:** #71 (Benchmark: corpus import set)
**Code under test:** `benchmark/corpus/*.muse.json` (10 entries) via the validator + harness.

Baseline coverage landed with the task: all 10 corpus files pass
`node tools/validate.mjs` against `schema/muse.schema.json` (verified at
authoring; full `npm test` 48/48 green).

## Behaviors to verify (remaining)

- **Corpus stays validating on schema evolution:** the harness's example loop
  scans `examples/` only — extend `tools/test.mjs` (or a dedicated
  `tests/corpus.test.mjs`) to run the same schema + cross-ref + semantics
  checks over `benchmark/corpus/*.muse.json` so a schema tightening can't
  silently rot the corpus.
- **Re-import determinism:** re-running `node importer/cli.mjs` on each
  `sources/` file yields a document that still validates (provenance
  timestamps will differ; content should not drift). Worth a smoke test on a
  small subset (the chorales) rather than the heap-heavy Haydn movements.
- **README table accuracy:** entry count and file list stay in sync
  (guard: README table row count == corpus file count).
- **Provenance invariant:** every corpus file carries an `event: "import"`
  provenance entry with `ai: false` (project policy; ajv can't assert it).

## Notes

- Parser heap-scaling note (README): Haydn mvts 1/4 need
  `--max-old-space-size` ≥ 8192/16384. If a corpus re-import CI step is ever
  added, it must set the flag or the task will OOM.
- The metrics harness (#72) is the corpus's primary consumer; wire ≥2
  entries there when it lands.

## How to run

`npm test` once the corpus loop lands; directly:
`for f in benchmark/corpus/*.muse.json; do node tools/validate.mjs "$f"; done`

---

## Closed — 2026-08-22 (issue #78)

Coverage landed: `tests/corpus.test.mjs` — 46 checks:

- All 10 corpus entries validated through the same three channels as the
  harness example loop: root schema (real CLI), `danglingRefs`, semantics.
- Provenance invariant: every entry carries `event: "import"` with
  `ai: false`.
- README table accuracy: row count == file count; every file listed.
- Re-import determinism smoke (bwv269, bwv316): re-imported output validates
  and is content-identical modulo per-import freshness (provenance `at`,
  `metadata.created`, the fresh work ULID — pinned as the only sanctioned
  drift). Haydn excluded per the README heap-scaling note.

The metrics-harness wiring note is already satisfied: #72 landed
`benchmark/metrics.mjs` scoring ≥2 corpus entries in
`tests/benchmark.test.mjs`.

Run: `npm test`.
