# Test spec — Frontend QA Tier 3 (task #184)

Written 2026-08-24 by the completing agent, per TASK_WORKFLOW §6.
Code under test: `tools/qa_frontend/tests/test_live_smoke.py` +
`.github/workflows/live-smoke.yml`.

## How to invoke

```bash
QA_LIVE=1 python3 -m pytest tools/qa_frontend/tests/test_live_smoke.py -q
```

## Coverage landed with the task

- **/explorer/ 200** on the live dev-- deploy
- **data/works.json** valid, 13 works, pinned fields present
- **piano-roll PNG** 200 with content length
- **zero console errors** headlessly on the live page
- **live interaction** (click through to detail and back)
- Local runs skip by default (QA_LIVE=1 gate); CI runs on a 6-hour
  schedule + workflow_dispatch.

## Cadence decision (documented per issue)

On-deploy polling via the Netlify status API was the alternative; the
6-hour schedule is the simpler, hook-free floor that still catches a
broken deploy within a workday. An on-deploy trigger can be added later
via Netlify's outgoing webhook → GitHub repository_dispatch.

## Behaviors still needing coverage (follow-up)

- **Deploy-triggered run** — schedule → webhook-driven (above).
- **Failure notification** — a failing live smoke currently fails the CI
  job silently; a Slack/issue notification is the escalation path.
- **Spike listener smoke** — /spike/ shares the deploy; its audio assets
  get the same treatment when P2 lands.
