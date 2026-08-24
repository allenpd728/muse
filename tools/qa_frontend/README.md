# qa_frontend — Tier 2 headless DOM tests

Playwright + headless Chromium against a local static server. The explorer
page executes for real: the work-list populates, row clicks render detail,
piano-roll images resolve, the fetch-failure fallback shows, and console
errors fail the suite.

## Setup (one-time)

```bash
pip install playwright
python3 -m playwright install chromium
```

## Tests

```bash
cd tools/qa_frontend && python3 -m pytest   # 10 tests, ~7s
```

Registered in `tools/run_tests.sh` as a slow-tier suite (Chromium download
is a one-time environment cost; CI caches it).

## Coverage

- work-list populates (13 rows), per-row parts/notes meta
- row click renders detail (stats grid, pattern table, part names)
- piano-roll `<img>` resolves (naturalWidth > 0)
- back button returns to the list
- fetch failure → visible error fallback (route-aborted JSON)
- zero console errors on load
- data endpoint serves valid JSON
