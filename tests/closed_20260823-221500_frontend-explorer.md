# Test spec — Frontend explorer (task #164) — CLOSED

Written 2026-08-23 by the completing agent, per TASK_WORKFLOW §6.
Code under test: `tools/muse_explorer/` + `docs/explorer/`.

## How to invoke

```bash
python3 tools/muse_explorer/generate.py        # regenerate artifacts
cd tools/muse_explorer && python3 -m pytest    # 6 tests, ~52s (quick mode)
```

## Coverage landed with the task

- **Artifact contract:** every work carries the pinned field set
  (IR summary, part names, pack stats, patterns, piano-roll path);
  registry coverage = 13 files.
- **Render contract:** committed PNGs are real, non-empty, magic-checked.
- **Determinism:** two quick generations produce identical JSON.
- **Freshness tripwire:** committed works.json must equal regeneration.
- **DOM mount safety:** noindex meta, fetch fallback, no external runtime
  resources.

## Behaviors still needing coverage (follow-up)

- **Netlify deploy smoke** — the QA site's /explorer/ path is config-only
  until the next deploy; a post-deploy curl check belongs to #163 (CI).
- **Audio wiring** — P2 renders land → per-work audio player; pin the
  player element's presence once the first WAV exists.
- **Pattern-detail drill-down** — the page shows counts only; a drill-down
  into top patterns per work would consume the full JSON from W3.
- **Visual review** — the founder's ear has no eye test yet; layout/color
  review is human QA on the QA URL.

## Resolution (Tests: #178, 2026-08-24, run=20260823-2312-h8pk)

4 tests added to `tools/muse_explorer/tests/test_explorer.py` (suite now 10,
green ~54s via runner fast tier):

- **All piano_roll references resolve** — every committed works.json entry's
  img path exists, is >1000 bytes, and has PNG magic (was: only bach_bwv227.1
  spot-checked).
- **W3→explorer pattern seam tripwire** — every committed work carries
  non-empty pattern counts; a report-format change that zeroes the regex
  merge fails loudly instead of silently emptying the page.
- **Pattern parser robustness** — missing report degrades to {} without
  crashing; malformed/prose lines are skipped, not coerced.

Deferred, with owners (not gaps in this task):

- Netlify deploy smoke → #184 (Frontend QA Tier 3)
- Audio wiring → P2 renderer (not landed)
- Pattern drill-down → page feature, needs its own task
- Visual review → human QA on the QA URL
