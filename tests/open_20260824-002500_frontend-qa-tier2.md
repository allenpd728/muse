# Test spec — Frontend QA Tier 2 (task #183)

Written 2026-08-24 by the completing agent, per TASK_WORKFLOW §6.
Code under test: `tools/qa_frontend/`.

## How to invoke

```bash
pip install playwright && python3 -m playwright install chromium
cd tools/qa_frontend && python3 -m pytest   # 10 tests, ~7s
```

## Coverage landed with the task

- **work-list populates** (13 rows, per-row parts/notes meta)
- **row click renders detail** (stats grid, pattern table, part names)
- **piano-roll resolves** (naturalWidth > 0)
- **back button** returns to the list
- **fetch failure** → visible error fallback (route-aborted JSON)
- **zero console errors** on load
- **data endpoint** serves valid JSON
- **Schubert row** renders the large formatted count (24,772)

## Behaviors still needing coverage (follow-up)

- **Live URL pass (Tier 3, #184)** — the same harness pointed at
  dev--muse-qa-58fd708e.netlify.app; that is #184's job, not this one's.
- **Workbench-page coverage** — when W-B3 lands, the same harness extends
  to the seed panel + probe panel (the mount safety test shape is the
  template).
- **Viewport/a11y sweep** — layout at mobile widths and keyboard nav are
  unpinned today.
- **Visual regression** — screenshot-diffing is a deliberate non-goal for
  v0 (QA page, not product surface); reconsider if the explorer becomes
  public-facing.
