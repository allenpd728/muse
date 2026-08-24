# Blocker — #224 (Tier 3 live smoke) conflicts with the founder's Netlify pause

**Filed:** 2026-08-24, run=20260824-2254-2185.
**Task attempted:** #224 — Tests: Frontend QA Tier 3 — live deploy smoke
(follow-ups to #184, spec `tests/open_20260824-003200_frontend-qa-tier3.md`).

## What's missing

A decision: does the founder's Netlify pause retire #224, or suspend it
until the deploy resumes?

## Why the work is unstartable

Every follow-up in the spec exercises the live deploy or its CI gate:

- deploy-triggered run (Netlify webhook → repository_dispatch)
- failure notification on the live-smoke CI job
- /spike/ listener smoke against live audio assets (P2 has landed)

But `netlify.toml` carries the founder's explicit deferral
(2026-08-24):

> [DEFERRED 2026-08-24] The founder has paused the Netlify QA site for
> now; resume later. Tier 3 live smoke (QA_LIVE=1) and the workflow's
> Netlify build gate are intentionally on hold — Tier 1 (static contract)
> and Tier 2 (headless DOM on 127.0.0.1:0) remain the live frontend QA
> path. … so agents do not accidentally re-trigger the deploy while
> looking at frontend QA.

Writing more live-deploy tests or landing the 6h CI schedule would do
exactly what the pause forbids. The spec (extend Tier 3) and the
founder's note (Tier 3 on hold) contradict; only the human can resolve
which stands.

## What is needed to unblock

One of:

- **Retire #224** — close it (and possibly supersede the spec) until the
  deploy resumes; or
- **Resume the deploy** — uncomment netlify.toml's gate, at which point
  #224 proceeds as written; or
- **Narrow #224** — e.g. land only the CI workflow file dormant
  (schedule disabled, workflow_dispatch only) so resume is one edit.

## Side note for whichever path is chosen

#184's done comment claims `.github/workflows/live-smoke.yml` was
committed — it never landed (silently gitignored at the time, the #213
bug; only `conformance.yml` is tracked). When Tier 3 resumes, the
workflow file itself still needs committing.
