# Test spec: live-Gemini fixture conformance pin (follow-up to #113)

**Source task:** #113 (Live E2E: Gemini expand → metrics → WAV)
**Code under test:** `interpreter/fixtures/live-gemini.muse.perf.json` — a real
model-produced performance document (gemini-3.6-flash, 2-attempt loop). It is
the reference shape future adapters are compared against, so it must not rot:
schema or metric changes that invalidate it should fail loudly, not silently
strand the fixture.

## Behaviors to verify

- **Schema validity:** the fixture validates against
  `schema/performance.schema.json` (same ajv setup as the harness) and passes
  `checkPerfRefs` — pin both, since the harness checked them at generation
  time.
- **Conformance pin:** `scorePerformance(examples/full.muse.json, fixture)`
  returns 1.0 for all four metrics (motif_recall, structure_fidelity,
  tempo_shapes, harmonic_fidelity). If a spec/metric change intentionally
  moves a score off 1.0, the fix is to regenerate the fixture (same command
  as #113) or amend it deliberately — never relax the pin to make CI pass.
- **Provenance shape:** `metadata.interpreter` is present with `model` and
  `at` — the harness-stamped provenance contract, pinned so a hand-edited
  fixture can't masquerade as model output.

## How to run

`npm test`; no network, no live key — the fixture is static.
