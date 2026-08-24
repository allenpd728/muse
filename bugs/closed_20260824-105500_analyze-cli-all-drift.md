# Bug (CLOSED — fixed by b5f99e9, #237) — muse_analyze test references dropped CLI flag (`--all`)

**Found:** 2026-08-24, run=20260824-1034-f7e8, while running the full tier
as gate evidence for #214.
**Issue:** #237.
**Disposition:** pre-existing drift between the analyzer CLI and its test;
unrelated to #214 (reproduces identically on the pre-change test file).

## Symptom

`tools/muse_analyze/test_muse_analyze.py::TestCLI::test_all_writes_analysis_report`
fails under `./tools/run_tests.sh --full`:

```
assert r.returncode == 0, r.stderr
E  AssertionError: usage: cli.py [-h] [--max-points MAX_POINTS] [--json JSON] [work_id]
E    cli.py: error: unrecognized arguments: --all
```

## Root cause

The test invokes `cli.py --all`, but the CLI no longer accepts `--all` —
the flag was dropped or renamed at some point and the test was not
updated. The failure was masked because the test is slow-marked
(formerly `MUSE_SKIP_SLOW`-gated) and local fast tiers never run the
analyzer suite; `--full` is allow-fail in CI.

## Fix (one of)

- Restore/alias `--all` in `tools/muse_analyze/cli.py` (test's expectation:
  runs every corpus work and writes docs/analysis-report.md); or
- Update the test to the CLI's current per-work invocation loop.

## Impact

`--full` tier is red: 1 failed in muse_analyze. The analysis-report
regeneration path the test guards is unverified.
