# Test spec — B3 status dashboard (docs/boardroom/status.html)

## Behaviors to verify

- **Phase status lines** for phases 0–5 with a status word (done/in progress/blocked/deferred) matching docs/pipeline.md's phase-gate statements.
- **Live counts rendered from the runner, not pinned**: the page fetches or embeds a generated stats JSON (suite count, test count, corpus works=13) — test asserts the page does NOT hardcode a stale count (grep the HTML for a digits-only "suites" claim and fail if it disagrees with the generated data file at test time).
- **Blocked items listed with their reason**: E3 (#211) and Tier-3 QA (#224) appear with their blocker names.
- **The frontier call-out**: Phase 4 gate ("one corpus work passes the founder's ear") visible.
- **Zero console errors**; graceful render if the stats JSON is absent (page shows "regenerate stats" note, no crash).

## Invocation

`cd tools && python -m pytest qa_frontend/tests/test_boardroom_status.py -q`

## Closed 2026-08-26 (#265, run=20260825-1033-cae1)

Page landed: phase table 0–5 consistent with pipeline.md, live counts
fetched from generated stats.json (never hardcoded — the HTML-vs-data
disagreement test enforces it), blockers #211/#224 with reasons, the
frontier call-out (Phase 4 ear gate), graceful degradation when the
stats file is absent (regenerate note, no crash).

Generator: tools/boardroom_stats.py (runner --list for suite count,
pytest --collect-only per fast-tier suite for test count, explorer
works.json for corpus count). Documented on the page and in this spec.

Tests: tools/qa_frontend/tests/test_boardroom_status.py (6). Lessons:
shared PageSession console_errors are cross-test state — per-test
listeners on the shared session's own pages keep the zero-errors bar
honest (the degradation test's aborted fetch must not poison the
happy-path test).
