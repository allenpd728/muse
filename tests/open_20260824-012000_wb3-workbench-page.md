# Test spec — W-B3 seed workbench page

**Task:** #187 (W-B3 — Seed workbench page)
**Written:** 2026-08-24

## What to verify

1. **Page structure**
   - `docs/workbench/index.html` exists; loads `data/seeds/index.json`
   - Per-seed: seed panel (params + philosophy) + probe panel (per-probe status)
   - Empty-state message when no seeds committed

2. **Probe artifact**
   - `data/seeds/bwv227.1.probes.json` exists; `ok: true`
   - Deterministic: re-running probes CLI yields identical JSON

3. **DOM mount safety**
   - Panels render for the committed seed; no JS exceptions on load
     (headless check)

## How to run

```bash
python3 tools/muse_probes/cli.py seeds/bwv227.1.seed.yaml --work corpus/bach/bwv227.1.mxl \
    > docs/workbench/data/seeds/bwv227.1.probes.json
# serve: python3 -m http.server -d docs/workbench 8000
```
