# Frontend QA — design doc scaffold

**Phase 2.5 — integration. Status: scaffold (awaiting sign-off).**

How the explorer (and any future static frontend) gets tested so agents can
QA the page themselves. Three tiers, ordered cheap → real.

## Tier 1 — Static contract (already landed, #164)

What exists: `tools/muse_explorer/tests/test_explorer.py` — artifact
contract (fields, registry coverage, determinism, freshness tripwire) and
DOM mount safety (noindex, fetch fallback, no external resources). This
catches data drift and missing-artifact bugs, but **never executes the
page**. Gap: the page's JS could be broken and Tier 1 still passes.

## Tier 2 — Headless DOM tests (proposed)

Run the page in a real browser engine (headless Chromium via Playwright)
and assert the rendered DOM:

- Page loads `index.html` from a local static server; `work-list` populates
  with 13 rows (fetch of `data/works.json` succeeds).
- Clicking a row renders the detail view: title, stats grid, part names,
  pattern table, piano-roll `<img>` that resolves (naturalWidth > 0).
- Back button returns to the list.
- Failure fallback: kill the JSON endpoint → page shows the error message
  instead of hanging on a blank screen.
- Console error capture: page must produce zero console errors on load.

Implementation: `tools/qa_frontend/` with a Playwright runner. Chromium
download (~150 MB) is a one-time environment cost; CI caches it. Runs in
the unified runner as a new suite. ~10–15 tests, all headless, no network
beyond localhost.

## Tier 3 — Live deploy smoke (proposed; DEFERRED 2026-08-24)

> **Deferred 2026-08-24.** The Netlify QA site is paused by founder decision;
> resume later. Tier 3 is on hold — the live site is not a working QA
> dependency until re-enabled (netlify.toml header comment tracks this).
> Tier 1 (static contract) and Tier 2 (headless DOM on 127.0.0.1:0) remain
> the frontend QA path; `QA_LIVE=1` is left as the resume switch.

Post-deploy verification against the QA URL itself:

- After a Netlify deploy of `dev` succeeds, poll
  `https://muse-qa-58fd708e.netlify.app/explorer/` until 200, then assert:
  page HTML contains the mount point, `data/works.json` is valid JSON with
  13 works, one piano-roll PNG returns 200, and a headless pass (Tier 2
  runner pointed at the live URL) finds zero console errors.
- Fails the CI job when the live page regresses — the deploy itself is
  the thing under test.

Implementation: a CI job in `conformance.yml` gated on deploy success
(Netlify deploy status API), or a standalone nightly job if deploy hooks
prove flaky. Needs the NETLIFY_PAT for deploy status polling; no write
scope.

## What "QA myself" means concretely

| Question | Tier that answers it |
|---|---|
| Is the data fresh/complete? | 1 (landed) |
| Does the page actually render and interact? | 2 |
| Is the live site broken right now? | 3 |

## Open questions (draft-level)

- Playwright (Node, mature) vs Selenium (heavier)? Recommend Playwright.
- Live smoke cadence: on-deploy (needs hook/status poll) vs. nightly?
- Should Tier 2 run against the committed artifacts or regenerate first?
  (Committed — regeneration is Tier 1's freshness tripwire.)

## Acceptance criteria

- An agent can run one command and know the page renders, clicks work,
  and the live deploy is healthy — without a human opening a browser.
