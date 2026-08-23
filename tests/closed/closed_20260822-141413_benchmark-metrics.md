# Test spec — Benchmark #72: conformance metrics harness

**Source task:** #72 (benchmark/metrics.mjs)
**Code under test:** `benchmark/metrics.mjs` (motifRecall, structureFidelity,
scorePerformance, referencePerformance); corpus `benchmark/corpus/`.

DoD coverage landed with the task: `tests/benchmark.test.mjs` — 27 checks
(all transform families, negative recall cases, repetition/deviation bounds,
corpus floor + corrupted, CLI report shape). This spec is for what remains.

## Behaviors to verify

- **Wire into interpreter validation loop:** the scope doc's constraint
  semantics pass (#65 follow-up) should call `scorePerformance` — when that
  integration lands, a fixture whose motif is dropped must make the retry
  loop fire with the metric's error detail.
- **Rhythm-only motif recall:** currently scored 0 with a reason ("no pitch
  contour") — a rhythm-grid recall (duration grid + accent pattern) is a
  real gap for percussion-first works; decide and pin.
- **Chord/texture fidelity:** recall is lead-contour only; harmonic-content
  recall (does the progression's pitch-class set appear per section) is
  unmeasured. Pin when a metric is chosen.
- **Structure beyond length:** only total bars are measurable from the perf
  layer; section-boundary detection (order/reorder conformance) needs
  section markers in the perf doc (candidate v0.x perf-format amendment —
  flag to spec owners before adding).
- **Score stability:** metric is exact-match + tolerance-free contours;
  microtiming in real LLM performances (onset_beat drift) may need onset
  snapping — pin tolerance policy after the first live-model benchmark run.

## How to run

`npm test`; CLI `node benchmark/metrics.mjs <schema> <perf>`.

---

## Closed — 2026-08-22 (issue #90)

Coverage landed:

- **Interpreter validation loop wired:** `interpreter/expand.mjs`'s
  `validatePerf` now runs `scorePerformance` — the constraint semantics
  pass from the scope doc. A dropped `must_contain` motif fails with
  `motif_recall` error detail, the feedback reaches the model on retry
  (2 new checks in `tests/interpreter.test.mjs`).
- **Rhythm-only motif recall:** duration-grid match (normalized, uniform
  aug/dim tolerated, same convention as pitch recall) — 4 checks.
- **Harmonic fidelity:** `harmonicFidelity()` — per section wired to a
  progression, every chord's pitch-class set must be covered (voicing
  irrelevant) — 4 checks; wired into `scorePerformance` as
  `harmonic_fidelity`.

Deferred (still open, with triggers):

- **Structure beyond length:** section-boundary conformance needs section
  markers in the perf doc — a v0.x perf-format amendment; flag to spec
  owners before adding (unchanged from the spec).
- **Score stability / onset snapping:** pin the tolerance policy after
  the first live-model benchmark run (unchanged).

Run: `npm test`.
