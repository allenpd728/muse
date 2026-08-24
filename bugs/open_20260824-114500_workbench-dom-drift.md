# Bug: qa_frontend workbench DOM tests drifted — /workbench/ index removed

- **Found:** 2026-08-24, run=20260824-1059-b671 (while working #223)
- **Owning issue:** #229 (Workbench UI QA: DOM + functionality tests)
- **Suite:** tools/qa_frontend (slow tier — the fast gate never runs it,
  which is how the drift went unnoticed)

## Symptom

`cd tools/qa_frontend && python -m pytest` → 19 failed, 18 passed,
5 skipped. All failures are in `tests/test_workbench_dom.py`,
`tests/test_workbench_interactions.py`, and `tests/test_growth_panel.py`
— every one navigates to `/workbench/`.

## Root cause

`docs/workbench/index.html` no longer exists. The W-B6/W-B7/W-B8 work
(master index shell, file explorer, terminal mode) replaced the single
workbench page with `terminal.html`, `detail.html`, and `files.html`;
`/workbench/` now serves a directory listing, so every assertion against
the old single-page DOM ("seed workbench" heading, seed/probe panels,
controls bar, era select, growth panel) fails.

## Repro

```bash
pip install playwright && python -m playwright install chromium
cd tools/qa_frontend && python -m pytest tests/test_workbench_dom.py -q
# test_workbench_page_loads: 'seed workbench' in 'directory listing for /workbench/...'
```

## Fix direction (for #229's owner)

Retarget the three files at the new page structure: terminal mode
(`terminal.html`) as the primary surface, `files.html` for the explorer,
`detail.html` for per-work detail — or pin the mount-safety shape per
page. The explorer Tier-2 tests (`test_explorer_dom.py`, `/explorer/`)
still pass and are the template.

Note: the fast tier doesn't run qa_frontend (slow suite), so DOM drift
lands silently — the runner-discovery contract (#217) registers the suite
but the gate cadence is the gap; consider a periodic slow-tier run.
