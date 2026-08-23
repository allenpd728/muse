# Test spec — unified test runner (Tests: issue #176)

Written 2026-08-23 by the completing session, per TASK_WORKFLOW §6.

## Status of coverage

16 pytest tests in `tools/test_runner_meta.py`, all passing:

- `--list` inventory carries every tools path with test files
  (inventory contract guards unregistered suites)
- unknown-flag exits with code 2
- C4 `tools/assertions/tests` registered in the runner (test was the
  driver — it caught the missing registration)

Run: `python -m pytest tools/test_runner_meta.py -q` (<1 s, no pytest-fast tier).

## Behaviors still needing coverage (gaps)

1. **Runner discovery contract on CI.** `--list` is fine as a
   registration check; the "when a new tool lands its suite must be
   registered" audit a CI job asserts, not a convention.
2. **Parallelism design.** Fast tier ~2.5 min serial; `pytest -n auto`
   or CI per-suite splits are worth a design note rather than a test.
3. **Slow-marker convention.** B9-scale tests are slow via the analyze
   suite, not via pytest.mark. An `-m slow` convention would make the
   split principled.

## Invocation

`python -m pytest tools/test_runner_meta.py -q` (sub-second).
