# Bug — workbench pages overflow horizontally at mobile width

**Found by:** run=20260916-1525-8d06 (TASK_WORKFLOW §1c in-flight defect log)
at 2026-09-16 ~16:02Z, while working #304 (workbench site navigation).
**Issue:** [#309](https://github.com/allenpd728/muse/issues/309) `status:available`.

## Symptom

At a 375px viewport the workbench pages scroll horizontally:

```
workbench/detail.html:   scrollWidth − clientWidth = 197px
workbench/terminal.html: scrollWidth − clientWidth =   5px
```

The overflow is committed behavior on `dev`, not introduced by #304 — the
nav adds 0px (it wraps; verified by stashing the #304 `docs/` changes and
re-measuring: identical 197px / 5px).

## Repro

```bash
cd tools
python3 - <<'EOF'
import sys; sys.path.insert(0, ".")
from qa_frontend.harness import PageSession, serve_static
with serve_static("../docs") as s:
    with PageSession() as ps:
        for rel in ("workbench/detail.html", "workbench/terminal.html"):
            p = ps.new_page(); p.set_viewport_size({"width": 375, "height": 812})
            p.goto(f"{s.url}/{rel}", wait_until="networkidle")
            print(rel, p.evaluate(
                "document.documentElement.scrollWidth - document.documentElement.clientWidth"))
EOF
```

## Root cause

`docs/workbench/detail.html` — the `.panel` grid collapses to one column at
`max-width: 900px`, but the `.card` children keep a 540px intrinsic width
because the seed/probe `<pre>` blocks do not shrink: `pre { overflow-x:auto }`
scrolls only once the parent is width-constrained, and the grid item's
default `min-width:auto` lets the `pre` set the column width. Offending
elements at 375px: `div.card` (right edge 572px, width 540px), its `h3`,
and the two `pre` blocks.

`docs/workbench/terminal.html` — a `.drawer button` overruns by 5px (right
edge 380px); the flex row wraps but the last button does not fit.

## Fix direction (not prescriptive)

Constrain the grid/flex items so children can shrink — e.g. `.card { min-width: 0 }`
plus the same on `.panel > *`, and `max-width:100%` on the `pre` blocks;
give the drawer buttons `flex-shrink` room or reduce padding at narrow
widths. `/index.html` and `/explorer/` already have mobile-overflow pins
(`test_pipeline_table_no_mobile_overflow`,
`test_mobile_no_horizontal_overflow`) — the workbench pages have none, so
the fix should add the equivalent pin.

## Related

- #304 (workbench navigation) — found in flight, no overlap in cause.
- `tools/qa_frontend/tests/test_pipeline_table.py::test_pipeline_table_no_mobile_overflow`
  and `test_explorer_viewport_a11y.py::test_mobile_no_horizontal_overflow`
  are the existing pins for the sibling pages.

_This bug report was created by an AI agent (OpenHands) on behalf of the repository owner._
