# CI retry - manual one-shot re-run of failed jobs (#293, #300)

Occasionally the conformance workflow fails for transient/flaky reasons
(network timeouts, runner provisioning hiccups, etc.) rather than a real
regression. The suite itself is the gate:the fast tier passes locally
(`./tools/run_tests.sh`), so a red runthat cannot reproduce locally is the
class of failure that deserves a retry before a human looks.


## Manual trigger: a human decides a failure is flaky

```bash
gh workflow run retry-flaky.yml -f run_id=<RUN_ID> --repo allenpd728/muse
```

or, equivalently, rerun directly:

```bash
gh run rerun <RUN_ID> --repo allenpd728/muse --failed
```

The workflow's single job validates that `run_id` is a numeric run ID,
then re-runs **only the jobs that concluded `failure`** in that run -- never
the whole pipeline (`gh run rerun <RUN_ID> --failed`). One invocation;
retrying again takes another explicit invocation.



## Why not automatic retry: GitHub's event model cannot make it safe

The original design (#293) retried automatically: `.github/workflows/
retry-flaky.yml` fired on `workflow_run` (conformance completed=failure,
first attempt, push events)and called `gh run rerun --failed`. Live
verification (#295) caught a **self-trigger loop**:our rerun command re-emits
the `workflow_run` event as a **brand-new run** - a fresh run id, with
the attempt counter reset to - so an attempt-count loop brake never
trips. 7 retry runs fired in ~45 minutes, each a failure, with no halt,
an Actions-minute burn loop (emergency-disabled on main. Any
such an event-triggered rerun topology on the same workflow is self-re-triggering by
GitHub's event model -- no guard can distinguish "this run is a retry"
from "this run deserves a retry". Auto-retry is therefore structurally
unsafe in this topology,and every loop iteration burns billing minutes. Hence
retry-flaky.yml is **workflow_dispatch-only**:an explicit human/agent
invocation is the only way it fires, one re-run per call.



## When to retry - and when not to

| Situation | Action |
|---|---|
| Run failed, fast tier passes locally (`./tools/run_tests.sh`)| Retry - flaky/runner-level cause |
| Run failed, local run also fails | Do not retry - real regression;fix the code, not the rerun |
| Retry also failed (same job twice)| Do not retry again - escalate: post the failing log in the issue |
| Conformance job failed for > 24 h straight | Do not retry - the runner is unlikely to recover; check repo/hosting settings |

The 24 h rule exists because retries are cheap but not free: they consume
Actions minutes (billing)and can mask a systematic runner outage. The
manual dispatch model already prevents automation loops;the rule is about
*your* time, not a loop constraint.



## Design notes

- The workflow cannot edit `.github/` (workflow-content writes need a
  `workflow`-scoped token);it only *re-runs existing jobs*, which the
  default `GITHUB_TOKEN` grants (`actions: write`, per-job).
- **Placement:**`workflow_dispatch` needs no default-branch registration, but
  a byte-identical copy of `retry-flaky.yml` is **maintained on `main`**
  per the infra parity convention (workflow wiring is the one infra exception
  to the dev-only convention; keep the branches in sync -- one file, no
  logic drift).
- The workflow targets failed jobs of the named run only -- it may be used
  for any failing run ID (push-or-PR), as long as the invoker has
  `actions: write` and repo-scope.



- **Usage from a workflow/agent:**`gh workflow run retry-flaky.yml -f
  run_id=<ID> --repo allenpd728/muse` needs a token with `repo` scope
  (the agent token works. The dispatch input guard only accepts
  numeric run IDs;anything else fails before any rerun is issued.



- A rerun of a run that a previous invocation already retried is fine;each
  invocation is an explicit, auditable one-shot retry,and the Actions run
  history itself is the audit trail.