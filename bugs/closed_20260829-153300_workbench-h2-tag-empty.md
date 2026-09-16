# Bug — workbench h2 revision tag renders empty (DoD test fails on dev)

**Found by:** run=20260829-1513-09an (TASK_WORKFLOW §1c in-flight defect log) at 2026-08-29 ~15:33Z.
**Issue:** [#306](https://github.com/allenpd728/muse/issues/306) `status:done`; root cause found and fixed by run=20260916-1525-8d06 on 2026-09-16.

## Symptom

`tools/qa_frontend/tests/test_workbench_dod.py::test_seeded_work_renders_heading_and_passing_tag`
fails on `dev` baseline:

```
>       assert tag.inner_text() == "passing"
E       AssertionError: assert '' == 'passing'
```

The h2 revision heading's `.tag` reads empty (`''` instead of `passing`).

## Repro

```bash
cd tools
python3 -m pytest qa_frontend/tests/test_workbench_dod.py::test_seeded_work_renders_heading_and_passing_tag -q
```

Fails **without** any new work from this session (verified by moving the new
test file aside and re-running — still fails). Also fails twice in a row with / without
the addition, so not a flake introduced by the collapse work.



## What is known

- All four committed probe artifacts have `ok=True`
  (`bwv227.1{,.v2,.v3,.v4}.probes.json`), so the `probes && probes.ok ? 'passing' :
  'no probes'` template term should render `passing` for every revision row.
- The page renders 4 `details.wb-rev` rows (one base + v2/v3/v4), each with an
  `<h2>…<span class="tag ok">…</span></h2>`.

## Root cause

**The page was correct; the test's assertion was wrong.** Determined
2026-09-16 (run=20260916-1525-8d06), fixed in the same session.

Since #303/fad374c each seed revision is a `details.wb-rev` row and only
the first is open. Elements inside a *closed* `<details>` are not rendered,
and Playwright's `inner_text()` reads rendered text. Measured on the page:

```
heading 0  open=True   inner_text="passing"   textContent="passing"   class="tag ok"
heading 1  open=False  inner_text=""          textContent="passing"   class="tag ok"
heading 2  open=False  inner_text=""          textContent="passing"   class="tag ok"
heading 3  open=False  inner_text=""          textContent="passing"   class="tag ok"
```

The test looped over **all** headings (`for i in range(headings.count())`)
but asserted with `inner_text()`, so it could only ever pass for the one
open row. Not a race, not strict-mode: deterministic given the collapse
behavior. (`test_seeded_work_shows_all_four_panels` passes because it reads
the *first*, open row only.)

The original hypothesis in this file (an `inner_text` timing or strict-mode
locator mismatch) was on the right axis — `inner_text` vs. visibility — but
the mechanism is the closed-`details` render state, which is stable.

## Fix

`text_content()` in place of `inner_text()`, plus a docstring recording why
(the DOM carries the tag regardless of open state). Verified non-vacuous:
with the probe JSON aborted the page renders no `.work h2 .tag` at all, so
the assertion still catches a genuinely missing tag.

Fix commit: lands with #306.

## Closed 2026-09-16 (#306, run=20260916-1525-8d06)

`text_content()` in place of `inner_text()` in
`tools/qa_frontend/tests/test_workbench_dod.py::test_seeded_work_renders_heading_and_passing_tag`,
with a docstring recording the closed-`details` render-state reason.
`qa_frontend/tests/test_workbench_dod.py` -> 7 passed; full qa_frontend
suite green (118 passed, 5 skipped, 0 failed — the last red test on `dev`).
Verified non-vacuous: with the probe JSON aborted no `.work h2 .tag`
renders, so the assertion still fails on a genuinely missing tag.
## Related

- Existing workbench DoD tests: `test_seeded_work_shows_all_four_panels` passes,
  `test_era_filter_preserves_work_index` passes — this is the only failing
  DoD test on `dev` at hand-off time (101 passed, 1 failed, 5 skipped in
   the qa_frontend suite).

_This bug report was created by an AI agent (OpenHands) on behalf of the repository owner._