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

---

## Closed 2026-08-24 (issue #223, run=20260824-1059-b671)

Landed coverage: `tools/qa_frontend/tests/test_explorer_viewport_a11y.py`
(6 tests), closing the viewport/a11y gap on the explorer surface:

- **Mobile (375px)** — no horizontal overflow; list populates (13 rows)
  and row tap renders detail.
- **Desktop (1280px)** — content column capped (≤940px incl. padding) and
  centered.
- **A11y** — `<html lang="en">` declared; piano-roll img carries an alt
  naming the work; the back button is keyboard-operable (focus + Enter
  dismisses the detail).

Deliberately not pinned: `.work-row` divs are click-only (no tabindex) —
keyboard users can't open a work; that's a page-owner decision for the
QA surface (v0), not a silent pin.

Other follow-ups stand: live URL pass is Tier 3 (#224), workbench-page
coverage follows the W-B6/B7/B8 page structure — see the DOM-drift bug
logged this session (bugs/open_20260824-114500_workbench-dom-drift.md,
owned by #229): the sibling redesign removed `docs/workbench/index.html`,
leaving 19 workbench-side tests red. Visual regression stays a non-goal.

Gate: `cd tools/qa_frontend && python -m pytest tests/test_explorer_dom.py
tests/test_explorer_viewport_a11y.py` → 16 passed.
