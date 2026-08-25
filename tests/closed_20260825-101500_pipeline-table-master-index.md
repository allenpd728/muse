# Test spec — pipeline table on the master index page (issue #241)

Written 2026-08-25 by the completing agent, per TASK_WORKFLOW §6.
Code under test: `docs/index.html` pipeline section (static markup +
`.pipeline` CSS).

## How to invoke

```bash
pip install playwright && python3 -m playwright install chromium
cd tools && python3 -m pytest qa_frontend/tests/test_pipeline_table.py -q
```

## Coverage to land (behaviors the DoD requires)

- **Seven rows in fixed order** — package, unzip/decode, deterministic
  baseline, grow, validate, render, distill (stage-name cells).
- **Row shape** — per row: io cell (contains "→"), tool link, status
  (`status-done`/`status-missing` class), non-empty assets cell.
- **Grow row links the L1.1–L1.4 issues** (#206–#209) — a queue-state
  pin, not page decoration.
- **Tool links resolve to repo-tree paths** (github.com/.../tree/dev/tools/*)
  or issue URLs — caught when a tool dir renames.
- **Zero console errors** on `/index.html` with the table present
  (standard Tier-2 bar).

## Not applicable

- The table is static markup — no JS behavior to pin beyond the console
  check. D20 (no mockup content) is trivially satisfied and needs no
  test beyond the caption's presence.
