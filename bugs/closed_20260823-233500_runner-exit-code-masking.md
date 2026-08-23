# Bug (CLOSED — fixed by 4fcc582, #191) — unified test runner masks pytest exit codes

**Found:** 2026-08-23, run=20260823-2312-h8pk, while gathering gate
evidence for #165.
**Disposition:** fixed on `dev` at `4fcc582` (#191, closed status:done).

## Symptom

`tools/run_tests.sh` reports `PASS` for suites whose tests actually
failed, and exits `all suites green` (0) anyway. Live repro on dev @
69b4bcc: `PASS  assertions  1s  4 failed, 2 passed` — the line carries
the failure count and still prints PASS.

## Root cause

In `run_one()`:

```bash
out=$(python3 -m pytest "$dir" -q 2>&1 | tail -3)
rc=$?
```

`rc` captures the exit code of `tail` (the last command in the pipe), not
pytest's. Pipelines return the last command's status, so `rc` is 0
whenever `tail` succeeds — which is always.

## Fix

Capture pytest's exit code before the pipe, e.g.

```bash
out=$(python3 -m pytest "$dir" -q 2>&1); rc=$?; out=$(echo "$out" | tail -3)
```

or `set -o pipefail` at the top (already `set -u`; combining is fine).

## Impact

The unified runner is the CI substrate (#163). Until fixed, "all suites
green" is not evidence — every suite must be re-verified directly
(`cd tools && python3 -m pytest <suite> -q`) when a done claim cites the
runner as its gate. Pair with
`open_20260823-233500_assertions-cwd-relative-corpus-paths.md`: the
assertions suite's 4 real failures are currently invisible because of
this bug.
