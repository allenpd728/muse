# Test spec - CI retry redesign: dispatch-only one-shot (#300)

Written 2026-08-29 by the completing agent, per TASK_WORKFLOW §6.
Work under test: `.github/workflows/retry-flaky.yml` +
`docs/ci-retry.md` + `docs/pipeline.md` retry row.

Work supersedes the #293 auto-retry design (see tests/open_20260828-103836_
ci-flaky-retry.md for the superseded contract); #300 rewrites the workflow to
workflow_dispatch-only after live verification showed a self-trigger loop.



## Behaviors to verify

1. **Workflow parses as valid YAML** and is `workflow_dispatch`-only:
   - `"on"` contains exactly `workflow_dispatch`, no `workflow_run`
     trigger anywhere in the file.
   - Dispatch input `run_id`: `required: true`, `type: number`.
2. **Arguments are correct:**
   - `permissions` block grants `actions: write` + `contents: read`.
   - The step validates `run_id` is numeric (rejects empty/non-digit with
     nonzero exit before any rerun,and then runs
     `gh run rerun "<run_id>" --repo <repo> --failed` - re-runs **only
     failed jobs**, never the whole pipeline.
3. **No guard epicycles:** the file contains no `run_attempt` and no
   `workflow_run` - topological impossibility replaces the old attempt-count
   loop-brake.
4. **Docs contract** (`docs/ci-retry.md`):
   - Manual trigger documented:`gh workflow run retry-flaky.yml -f
     run_id=<RUN_ID> --repo <owner>/<repo>`, plus the equivalent direct
     `gh run rerun <RUN_ID> --repo <owner>/<repo> --failed`.
   - "Why not automatic" section explains the self-trigger-loop failure
     mode (event-model cannot make auto-retry safe here; burning billing
     minutes;,and the dispatch-only consequence.

   - When-to-retry / when-not-to matrix retained (`run failed but local
     passes` -> retry; `local also fails` -> fix, not retry; `retry also
     failed` -> escalate; `> 24 h` -> don't mask systemic outage..
   - `docs/pipeline.md` retry row tracks both #293/#300|.
5. **Live behavior** (real gate; manual/opportunistic, depends on the
   runner issue #194):
   - `gh workflow run retry-flaky.yml -f run_id=<ID> --repo allenpd728/muse`
     triggers exactly one run that re-runs only the named run's failed jobs.
   - A second invocation re-runs again (each explicit invocation
     one-shot); no run can trigger another run itself..



## How to invoke

```bash
# static contract (fast tier, no network:
python3 -m pytest tests/docs -q
```

Gate evidence (from the completing agent): `./tools/run_tests.sh
--jobs 1` -> "all suites green" incl. docs suite (12 passed; the 5
pins in tests/docs/test_ci_retry.py pass;. YAML parses via
`python3 -c "import yaml; yaml.safe_load(open(
'.github/workflows/retry-flaky.yml'))"`.

Live verification ((after a real manual dispatch:
```bash
gh workflow run retry-flaky.yml -f run_id=<RUN_ID> --repo allenpd728/muse
gh run list --repo allenpd728/muse --workflow retry-flaky.yml
gh run view <retry-run-id> --repo allenpd728/muse --log
# confirm:the step ran 'gh run rerun <conformance-id> --failed' and
#only failed jobs of the named run were re-run; no new runs fire beyond
#the invoked one..
```



## Deliberately not covered by CI automation

The static pins above are the repo-side gate. Live dispatch semantics need
a healthy Actions runner (#194); exercised opportunistically, not on
every push.
## Resolution (2026-08-29, run=20260829-0207-sDt0)

Static pins verified green on dev head 7bbd781: tests/docs/test_ci_retry.py - 5 passed.

Live dispatch verification deferred: Actions runner not yet healthy (5 consecutive conformance failures incl. 02:08Z push run; #194 blocker closed but runner still failing).

Per when-not-to matrix (>24h straight, donot mask outage) + #295 precedent (live deferred until runner healthy), no bounded dispatch fired this session.

Follow-up: fire `gh workflow run retry-flaky.yml -f run_id=<ID> --repo allenpd728/muse` when a conformance run fails but runner logs are healthy; confirm one-shot rerun of failed jobs only, no self-triggered retry runs.



_This note was appended by an AI agent (OpenHands) on behalf of the repository owner._

