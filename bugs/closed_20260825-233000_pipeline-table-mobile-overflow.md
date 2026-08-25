# Bug — pipeline table overflows mobile viewport on /index.html

**Found:** 2026-08-25, run=20260825-1033-cae1, during a self-review pass.
**Introduced by:** 59559f8 (#241, same day).

## Symptom

`/index.html` overflows horizontally at 375px: page scrollWidth exceeds the
viewport by **431px** (the pipeline table renders 774px wide). Root cause:
`td.io { white-space: nowrap }` in the table CSS I shipped with #241 —
io cells can't wrap, so the table forces page-level horizontal scroll on
phones.

## Fix

Drop the `nowrap`, let io cells wrap, and add `overflow-x: auto` on the
`.pipeline` section as the containment floor (a genuinely long row scrolls
inside the section instead of the page).

## Verification

`tools/qa_frontend/tests/test_pipeline_table.py::test_pipeline_table_no_mobile_overflow`
— 375px viewport, page-level overflow must be ≤ 0. (Also surfaced the
harness rule: nesting `sync_playwright` sessions in one module is illegal
— reuse the module-scoped session.)

## Notes

Not filed as an issue: author-present fix, one CSS line, regression test
landed in the same commit.
