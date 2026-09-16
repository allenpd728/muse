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


## Update 2026-09-16 (run=20260916-1525-8d06): the premise was wrong

**The pause was never in effect.** This blocker reasons from the
`netlify.toml` note claiming the founder "paused the Netlify QA site". That
note was written, but the site was not actually paused: `muse-qa-58fd708e`
was still wired to auto-deploy the **dev** branch, and every push to dev
started a build at `context=production`. Confirmed against the deploy list —
each of `c3849fa`, `694e7ea`, `c78cfb9`, `a11c4e2`, `45c10f2`, `79eecd1`,
`6c2f902`, `996b499`, `07b9527`, `55ef31b` produced a deploy.

So for three weeks the repo carried a note saying "do not re-trigger the
deploy" while the deploy was triggering on every push. A doc asserting a
state the system was not in — the same failure mode as the #306 misdiagnosis
(a hypothesis recorded as if it were a finding) and the `**done**` status
claims the T7 lint now checks.

**The pause is now real and enforced at the API level** (2026-09-16):
`build_settings.stop_builds = true` on site
`84c6f54c-1f65-40bb-99dc-4e4f73730ff3`, verified by a push to dev producing
no new deploy. `netlify.toml` now states the actual configuration and the
one-line re-enable command.

## Effect on this blocker

It stays **open**, and its question is now sharper rather than answered:

- The founder's stated intent (2026-09-16: stop the builds, they were wasting
  credits) resolves the *contradiction* in favour of the pause. #224 remains
  correctly suspended, so no live-deploy tests should be written yet.
- Whether to **retire** #224 or keep it **suspended** is still the human's
  call — but it is now a clean choice, because the "resume the deploy" option
  is explicitly off the table for cost reasons.
- The **third option (narrow #224)** is unchanged and remains the cheapest
  path: land the live-smoke workflow file dormant (workflow_dispatch only, no
  schedule, no push trigger) so resuming is one edit and costs nothing while
  disabled. That also closes the side note below — the workflow file still
  needs committing.

Recommendation: take the narrow option now (it is inert and makes the spec's
work resume-able in one edit), and leave retire-vs-suspend for whenever the
deploy question is revisited. Not taken unilaterally here because it is
#224's own deliverable, not this blocker's, and #224 is `blocked-needs-input`.


## RESOLVED 2026-09-16 (run=20260916-1525-8d06): #224 retired, Netlify removed

This blocker asked whether to retire or suspend #224. Both options assumed a
hosted deploy would exist again. The founder's decision was to remove Netlify
from the project entirely, which settles it: **#224 is retired, not
suspended.**

Retired, concretely:

| Removed | Note |
|---|---|
| `netlify.toml` | deleted |
| `tools/qa_frontend/tests/test_live_smoke.py` | deleted (the Tier 3 test) |
| Netlify site builds | stopped at the API (`stop_builds = true`, `muse-qa-58fd708e`) |
| Tier 3 references in live docs | rewritten as retired (`docs/design/frontend-qa.md`, `docs/pipeline.md`, the boardroom status page) |
| `QA_LIVE` gate | gone with the test; a `tests/docs` guard now fails if it reappears |

`tests/open_20260824-003200_frontend-qa-tier3.md` is kept as the design record
of what Tier 3 would have been, marked RETIRED, and now points at what covers
its intent instead (the expanded Tier 2 suite: site links, anchor fragments,
mobile widths).

The blocker's own "side note" is also closed: `.github/workflows/live-smoke.yml`
never landed and no longer should — a guard test asserts no workflow references
Netlify, deploys, or `repository_dispatch`.

Why retiring rather than reviving: the deploy only published `docs/` so a human
could look at it. It cost a build on every push to `dev` for three weeks while
`netlify.toml` claimed the site was paused — measured at ten pushes, ten
deploys, `context=production`. Tier 2 already executes every served page, so
the hosted deploy added cost without adding a distinct check. If a hosted
preview is ever wanted, stand it up deliberately on its own branch and add the
smoke then.

This is a **blocker-resolution**: the issue (#224) is closed and the file is
renamed `closed_`.
