# Test spec — unified test runner (task #167)

Written 2026-08-23 by the completing agent, per TASK_WORKFLOW §6.
Code under test: `tools/run_tests.sh`, `tools/requirements.test.txt`.

## How to invoke

```bash
pip install -r tools/requirements.test.txt
./tools/run_tests.sh            # fast tier
./tools/run_tests.sh --full     # incl. slow suites
./tools/run_tests.sh --list     # inventory, no run
```

## Coverage landed with the task

- **Fast tier green:** 12 suites, 392 tests, ~2.5 min, exit 0.
- **Full tier green:** + muse_analyze slow suite, ~5 min, exit 0.
- **Aggregate exit code:** non-zero when any suite fails (verified during
  development against the stale-artifact failure, which the runner caught —
  the first regression it found).
- **Dependency guard:** missing pytest fails with an install hint, not a
  cryptic per-suite error.

## Behaviors still needing coverage (follow-up)

- **Self-test for the runner itself** — landed in #176
  (`tools/test_runner_meta.py`, 18 passing as of #214).
- **Runner registration as part of the task DoD** — covered by the
  meta-test's inventory assertion; wiring the meta suite into the runner's
  own SUITES list is #217's scope.
- **Parallelism** — landed in #214: suites run concurrently, capped by
  `--jobs N` (default nproc, ≤8; `--serial` for debugging). Per-suite
  output buffered, report prints in suite order, aggregate exit code
  unchanged. Fast tier 3m45s → 1m46s on 4 cores.
- **Beethoven 9 slow marker** — landed in #214: `@pytest.mark.slow`
  registered in `tools/pytest.ini`; fast tier passes `-m "not slow"`,
  `--full` applies no filter. muse_roll's B9 budget test (already marked)
  is now deselected from fast; muse_analyze's `MUSE_SKIP_SLOW` skipif was
  converted to the marker (the env var is retired — the runner owns the
  split now).

## Closed 2026-08-24 (#214, run=20260824-1034-f7e8)

All four residual items landed or were accounted for above. Also fixed
in flight: the install guard's requirements path was repo-root-relative
after the runner's own `cd tools/`, so fresh sandboxes silently failed
every suite; and a duplicate `muse_mockup` SUITES entry ran the suite
twice. Gate evidence on the #214 done comment. Pre-existing `--full`
failures found during verification were logged separately
(`bugs/open_20260824-105500_*.md` → issues #237, #238).
