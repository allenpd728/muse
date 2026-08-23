# Test spec — Frontend explorer (task #164)

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
