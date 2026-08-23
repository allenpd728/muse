# Test spec — Batch 3 #23: interpreter prompt + expansion harness

**Source task:** #23 (interpreter/expand.mjs)
**Code under test:** `interpreter/expand.mjs`; fixture
`interpreter/fixtures/minimal-expansion.muse.perf.json`.

DoD coverage landed with the task: `tests/interpreter.test.mjs` — 16 checks
(fake-model expansion of minimal.muse.json, retry loop with feedback,
fail-loud bound, rendition resolution, prompt contents, parse strictness,
env config). This spec is for what remains.

## Behaviors to verify

- **Live-model smoke (manual, never CI):** one real expansion per provider
  adapter (anthropic + openai wire shapes) against minimal.muse.json,
  recorded as a fixture; the prompt/response wire shapes are otherwise
  untested by design (no live calls in `npm test`).
- **Constraint semantics pass:** the scope doc's second validation stage
  (motif recall against `must_contain`, register bounds, tempo within
  range) is not yet executable — the harness validates schema + part refs
  only. Implementing it is the fidelity-metric work; when it lands, the
  retry loop must feed its errors too, and a fixture with a motif-recall
  failure must retry.
- **Clock consistency:** perf docs from the interpreter must have
  seconds ⇔ beats agreeing under the emitted tempo_map (see #22's follow-up
  spec — same check, interpreter side).
- **Feedback size bound:** validation feedback is unbounded text today;
  pin a truncation policy if real models hit context limits.
- **CLI contract:** `npm run expand -- <doc> <rendition> <out>` exit codes
  (0 valid, 1 failure) and stderr summary — covered manually; pin if the
  CLI becomes the #25 demo path.

## How to run

`npm test`; live smoke documented in the closing note of this spec.

## Resolution

Residual coverage landed in `tests/interpreter-residual.test.mjs` (issue #65):
the clock-consistency semantic is now executable — `checkClockConsistency` in
`tools/semantics.mjs` (linear interpolation between tempo_map points, 1e-3s
tolerance for float dust). The interpreter's own fixture is proven consistent;
two-segment tempo_map, onset drift (and its duration drag), missing clocks,
and empty tempo_map are all pinned. Live-model smoke stays manual/never-CI
by design; the constraint-semantics pass (motif recall, register bounds) is
explicitly deferred to the fidelity-metric work per the spec. 6/6 standalone;
npm test 46/46 green.
