# Bug — assertions suite uses CWD-relative corpus paths

**Found:** 2026-08-23, run=20260823-2312-h8pk, while gathering gate
evidence for #165.
**Disposition:** filed #190 (`status:available`) 2026-08-23.

## Symptom

`tools/assertions/tests/test_vocabulary.py` passes only when invoked from
`tools/assertions/`. From `tools/` — where `tools/run_tests.sh` invokes
every suite — 4 of 6 tests fail:

```
FileNotFoundError: [Errno 2] No such file or directory: '../../corpus/bach/bwv227.1.mxl'
```

## Root cause

Corpus paths are string literals relative to the caller's working
directory (`load("../../corpus/bach/bwv227.1.mxl")`, lines 16/21/26/34)
instead of being anchored to `__file__` like every other suite:

```python
os.path.join(os.path.dirname(__file__), "..", "..", "corpus")
```

## Fix

Resolve corpus paths relative to the test file; then
`cd tools && python3 -m pytest assertions -q` must be green with a real
exit code. Full DoD on #190.

## Impact

Invisible today only because the runner masks exit codes (see
`open_20260823-233500_runner-exit-code-masking.md`). Once that bug is
fixed, this suite turns the fast tier red — fix both, this one first if
anything, so the runner fix lands on a green board.
