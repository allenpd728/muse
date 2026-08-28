# CI retry — auto re-run of failed jobs (#293)

Occasionally the conformance workflow fails for transient/flaky reasons
(network timeouts, runner provisioning hiccups, etc.) rather than a real
regression. The suite itself is the gate: the fast tier passes locally
(`./tools/run_tests.sh`), so a red run that cannot reproduce locally is the
class of failure that deserves a retry before a human looks.

## Automatic retry

`.github/workflows/retry-flaky.yml` watches the conformance workflow via
the `workflow_run` trigger and re-runs **only the failed jobs**
(`gh run rerun <ID> --failed`) when all of these hold:

- the triggering run concluded `failure`
- it was the run's **first attempt** (`run_attempt == 1`)
- it was a `push` event

The attempt guard is the loop brake: a retried run (attempt 2+, itself
failing) cannot trigger the retry workflow again, so each CI run gets at
most **one automatic retry** — bounded by construction, no infinite loops.


If the retry also fails, the run is left concluded-failure for a human; what
follows is the manual path below.



## Manual trigger (when a human decides a failure is flaky)

```bash
gh run rerun <RUN_ID> --repo allenpd728/muse --failed
```

Re-runs only the jobs that concluded `failure` in that run — never the
whole pipeline. The command needs a token with `repo` scope (the agent
token works). If the whole run needs a fresh start instead (e.g. the retry
workflow itself glitched), `gh run rerun <RUN_ID>` without `--failed`, then
the retry workflow caveats apply (its `attempt == 1` guard means it
will not mid-flight re-re-run a retried run; that is intentional,)

## When to retry — and when not to

| Situation | Action |
|---|---|
| Run failed, fast tier passes locally (`./tools/run_tests.sh`,) | Retry — flaky/runner-level cause |
| Run failed, local run also fails | Do not retry — real regression;fix the code, not the rerun |
| Retry also failed (same job twice) | Do not retry again — escalate: post the failing log in the issue |
| Conformance job failed for > 24 h straight | Do not retry — the runner is unlikely to recover; check repo/hosting settings |

The 24 h rule exists because automatic retries are cheap but not free:
they consume Actions minutes (billing) and can mask a systematic runner
outage. The auto-retry upper bound (one per run) already prevents
masking; the manual rule is about *your* time, not automation's.

## Design notes

- The workflow cannot edit `.github/` (workflow-content writes need a
  `workflow`-scoped token); it only *re-runs existing jobs*, which the
  default `GITHUB_TOKEN` grants (`actions: write`, per-job).
- It intentionally does **not** rerun on `pull_request` events yet — PRs
  from forks lack the Actions permission context that pushes get, and
  the trigger workflow's own run is what grants the permission to act.
  Extending to PRs is a follow-up once the push path is proven.

- Manual reruns of runs that were auto-retried already are fine; they are
  human-initiated and the audit trail is the Actions run history itself.