# Test spec — B3 status dashboard (docs/boardroom/status.html)

## Behaviors to verify

- **Phase status lines** for phases 0–5 with a status word (done/in progress/blocked/deferred) matching docs/pipeline.md's phase-gate statements.
- **Live counts rendered from the runner, not pinned**: the page fetches or embeds a generated stats JSON (suite count, test count, corpus works=13) — test asserts the page does NOT hardcode a stale count (grep the HTML for a digits-only "suites" claim and fail if it disagrees with the generated data file at test time).
- **Blocked items listed with their reason**: E3 (#211) and Tier-3 QA (#224) appear with their blocker names.
- **The frontier call-out**: Phase 4 gate ("one corpus work passes the founder's ear") visible.
- **Zero console errors**; graceful render if the stats JSON is absent (page shows "regenerate stats" note, no crash).

## Invocation

`cd tools && python -m pytest qa_frontend/tests/test_boardroom_status.py -q`
