# Bug — workbench h2 revision tag renders empty (DoD test fails on dev)

**Found by:** run=20260829-1513-09an (TASK_WORKFLOW §1c in-flight defect log) at 2026-08-29 ~15:33Z.
**Issue:** [#306](https://github.com/allenpd728/muse/issues/306) `status:available`.

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

Not yet determined. Hypothesis: a DOM/`inner_text` timing or
strict-mode locator mismatch (the test's `heading.nth(i).locator(".tag")` may resolve to
an empty sibling in some rows, or the probes JSON load races the heading render).
Needs a dedicated fix task to investigate.

## Related

- Existing workbench DoD tests: `test_seeded_work_shows_all_four_panels` passes,
  `test_era_filter_preserves_work_index` passes — this is the only failing
  DoD test on `dev` at hand-off time (101 passed, 1 failed, 5 skipped in
   the qa_frontend suite).

_This bug report was created by an AI agent (OpenHands) on behalf of the repository owner._