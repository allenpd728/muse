# Test spec: E2 — The venue (event plan doc, issue #210)

The deliverable is a document (`docs/design/e2-the-venue.md`), so coverage is
mechanical doc-coherence: the plan must keep satisfying the issue's
Definition of Done, and the three status caches (design doc, design index,
pipeline) must not drift apart. A future edit that drops a DoD section or
downgrades the plan silently should fail.

## Behaviors to verify

1. **DoD sections present.** `docs/design/e2-the-venue.md` contains, as
   markdown headings: `## Venue option`, `## Staging mechanics for live LLM
   deliberation`, `## Projection design`, and a rights section covering
   provenance + the manifest conventions (heading matching
   `Provenance + rights`).
2. **Plan content pins.** The venue section names a recommended option;
   the staging section addresses live deliberation pacing (mentions
   deliberation windows); the rights section references the manifest
   (`ai_involvement`) and the no-artist-lookalikes rule.
3. **Status coherence.** The design doc's `Status:` line, the E2 row in
   `docs/design/index.md`, and the E2 row in `docs/pipeline.md` agree on
   state (all say draft/done with #210 referenced; none says `scaffold` or
   bare `filed`).
4. **Downstream contract intact.** The doc keeps E3 non-goals explicit
   (broadcast/distribution out of scope) and retains the recording-rights
   requirement for the venue agreement (E3 dependency).

## How to invoke

Implement as a small pytest suite (suggested location:
`tests/docs/test_e2_venue_plan.py` or alongside the other doc tests if a
docs suite exists by pickup time). Pure text assertions on the three files
above — no fixtures, no network. Wire into `tools/run_tests.sh` fast tier
if a docs-tests suite is registered there; otherwise standalone
`python -m pytest tests/docs/test_e2_venue_plan.py -q`.

## Edge cases

- Heading text edits that keep meaning (e.g. rewording) should not
  over-pin: match on the stable keywords above, not full lines.
- The doc may later promote from `draft` to `final` — the coherence check
  should accept any non-`scaffold` promoted state, and fail only on
  disagreement between the three caches.

## Closed 2026-08-24 (#230, run=20260824-2254-2185)

Landed in `tests/docs/test_e2_venue_plan.py` (7 tests), wired into the
runner as the `docs` suite (`../tests/docs` — the first registered suite
outside tools/):

1. DoD sections present (Venue option / Staging mechanics / Projection
   design / Provenance + rights, keyword-matched headings).
2. Plan content pins (named recommendation + capacity, deliberation
   pacing, `ai_involvement` + no-lookalikes).
3. Three-cache coherence (doc Status line, design index row, pipeline
   row — all promoted, none scaffold/filed, all reference #210).
4. E3 downstream contract (broadcast non-goal, venue-agreement recording
   rights).

Sensitivity verified by mutation testing: removing the recommendation,
regressing the pipeline row to `scaffold`, and dropping the manifest
reference each fail their pin. Suite runs in <0.1s; invocation:
`python3 -m pytest tests/docs/test_e2_venue_plan.py -q` or
`./tools/run_tests.sh` (fast tier, `docs` row).
