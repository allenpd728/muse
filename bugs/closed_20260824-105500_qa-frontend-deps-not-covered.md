# Bug (CLOSED — fixed by this commit, #238) — runner dep guard doesn't cover qa_frontend (playwright)

**Found:** 2026-08-24, run=20260824-1034-f7e8, while running the full tier
as gate evidence for #214.
**Issue:** #238.
**Disposition:** the runner's dependency guard
(tools/requirements.test.txt) is documented as "the source of truth" for
suite deps, but qa_frontend's playwright requirement was never added —
`--full` fails at collection on any fresh environment.

## Symptom

```
ERROR collecting qa_frontend/tests/test_explorer_dom.py
E  ModuleNotFoundError: No module named 'playwright'
(5 errors — all three qa_frontend test modules)
```

## Root cause

`tools/qa_frontend/README.md` lists the real setup:

```
pip install playwright
python3 -m playwright install chromium
```

Neither the package nor the browser-install step is wired into
requirements.test.txt / the runner's install guard. The suite entered
SLOW_SUITES without its deps following it.

## Fix

Add `playwright` to tools/requirements.test.txt and teach the runner's
install guard to run `python3 -m playwright install chromium` when the
qa_frontend suite will run (full tier only — keep the fast tier free of
the ~150MB browser download), or gate the suite on browser presence with
a clear skip message.

## Impact

`--full` tier is red on every environment that hasn't done the manual
README steps; the T2 headless-DOM gate (#183) only works on machines
where someone happened to install chromium.
