# Bug — explorer work rows not keyboard-focusable

**Found:** 2026-08-24, run=20260824-1056-xtbc, while working Tests:
Frontend QA Tier 2 (#223, spec tests/open_20260824-002500_frontend-qa-tier2.md
follow-up "viewport/a11y sweep").

## Symptom

The explorer's work rows are `<div class="work-row">` elements with an
`onclick` handler and no `tabindex`, so keyboard users cannot reach or
activate them: after the page loads, the only tabbable element in the
detail view is the back button; rows have `tabIndex === -1`.

## Repro

```bash
cd tools/qa_frontend && python3 -m pytest tests/test_explorer_viewport_a11y.py
# or manually: Tab through docs/explorer/ — focus never lands on a work row
```

## Root cause

docs/explorer/index.html builds rows as plain divs
(`row = document.createElement('div'); row.onclick = ...`). Divs are not
in the tab order and have no keydown handling.

## Fix (one of)

- Render rows as `<button class="work-row">` (restyle to match), or
- Add `tabindex="0"`, `role="button"`, and Enter/Space keydown → show(w).

## Impact

Mouse/touch unaffected (Tier 2 suite passes); keyboard-only and
screen-reader users cannot open any work detail. The explorer is a QA
surface today, but W-B3's workbench page copies interactive patterns from
it — fix before the pattern spreads.
