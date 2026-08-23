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

- **Self-test for the runner itself** — a meta-test that runs `--list` and
  asserts every tools/* dir with test files appears (guards against a new
  tool landing without runner registration).
- **Runner registration as part of the task DoD** — when #163 (CI gate)
  lands, "the runner discovers your suite" should be enforced by the CI
  job, not by convention.
- **Parallelism** — suites are serial today; `pytest -n auto` or per-suite
  job-level parallelism in CI would cut the 2.5 min fast tier substantially.
- **Beethoven 9 slow marker** — B9-scale tests are implicitly slow via the
  analyzer suite; an explicit `-m slow` convention would make the split
  principled rather than per-suite.
