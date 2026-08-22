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
