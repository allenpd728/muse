# Test spec — runner parallelism + slow marker (Tests: #214)

Written 2026-08-24 by the completing agent, per TASK_WORKFLOW §6.
Code under test: `tools/run_tests.sh` (parallel engine, flag parsing,
`-m "not slow"` fast-tier filter), `tools/pytest.ini`.

## How to invoke

```bash
cd tools && python3 -m pytest test_runner_meta.py -q
```

## Coverage already in place

`tools/test_runner_meta.py` (18 passing) covers: `--list` inventory
completeness, unknown-flag exit 2, FAIL-only-on-real-failure labeling.
All pass against the parallel engine.

## Behaviors needing coverage

- **Flag parsing** — `--jobs` with no argument, non-numeric, and `0` all
  exit 2; `--serial` is accepted and equivalent to `--jobs 1`; `--full`
  still composes with the other flags.
- **Parallel report order** — run with `--jobs 4` against two synthetic
  suites with deliberately different durations; assert the report prints
  in SUITES order, not completion order.
- **Aggregate exit code** — with a synthetic failing suite among N passing
  ones, exit code equals the failure count (unchanged semantics).
- **Slow-marker split** — a synthetic suite containing one
  `@pytest.mark.slow` test: fast mode reports it deselected; `--full`
  runs it. (Guards the `-m "not slow"` wiring; the marker registration
  itself is one pytest.ini read.)
- **Install-guard path** — guard resolves requirements against the script
  dir, not cwd (regression: it used a repo-root-relative path after the
  runner's own `cd tools/` and silently failed every suite in a fresh
  sandbox). Simulating a dep-less python is awkward; a static assertion
  that the guard references `$SCRIPT_DIR/requirements.test.txt` and exits
  2 on install failure is acceptable.

Synthetic suites belong under a tmp dir the meta suite creates — do NOT
register them in the real SUITES list.

## Closed 2026-08-24 (#239, run=20260824-2254-2185)

Landed in `tools/test_runner_parallel.py` (8 tests), invoked like the
meta suite: `cd tools && python3 -m pytest test_runner_parallel.py -q`.

- **Flag parsing:** `--jobs` with no argument / non-numeric / `0` →
  exit 2; `--serial --list` composes.
- **Parallel report order:** synthetic slow-first/fast-second pair under
  `--jobs 4` prints in suite order with wall time < serial bound (the
  runner copy is table-patched, so the shipped engine is what runs).
- **Aggregate exit code:** one failing suite among two passing → exit 1,
  `1 suite(s) failed` on stderr, PASS/FAIL rows in declared order.
- **Slow-marker split:** synthetic suite with one `@pytest.mark.slow`
  test — fast run reports `1 passed, 1 deselected`, `--full` reports
  `2 passed`.
- **Install-guard path:** static assertion that the guard references
  `"$SCRIPT_DIR/requirements.test.txt"` and exits 2 on install failure.

Mechanism note: synthetic suites are exercised by copying `run_tests.sh`
to a tmp dir with SUITES/SLOW_SUITES tables regex-replaced by absolute
tmp paths — the parallelism, buffering, exit-code, and marker behavior
under test is the shipped code. The synthetic suites themselves are
never registered in the real tables.
