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

---

## Closed 2026-08-24 (issue #217, run=20260824-1059-b671)

Landed coverage: `tools/test_runner_meta.py` grew to 19 tests. The key
addition is gap 1 as an assertion, not a convention:

- **Discovery contract** (`test_discovery_contract_all_test_files_registered`):
  walks `tools/` for `test_*.py` (excluding `spike/`, `__pycache__`, and
  the meta suite itself) and asserts every file is covered by a `--list`
  entry. A new tool landing without registration now fails the meta suite
  on its own — no hardcoded list to maintain.

The contract immediately caught three live violations, fixed in the same
commit: **muse_budgets** (9 tests) and **muse_event** (4 tests) were
never registered, and **muse_decode/test_decode.py** (top-level) was
uncollected because the entry pointed at `muse_decode/tests` — entry
widened to `muse_decode`. All three now run in the fast tier.

Gaps 2–3 (parallelism design note, `-m slow` convention) are sibling
scope under the claimed #214 runner-residuals item — deliberately not
duplicated here.

Gate: `python -m pytest tools/test_runner_meta.py -q` → 19 passed;
`./tools/run_tests.sh` fast tier → all suites green (incl. the two
newly registered suites).
