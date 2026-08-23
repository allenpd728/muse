# Test spec — S3.5 assertions — CLOSED

**Task:** #146 (S3.5 — Assertions)
**Written:** 2026-08-23

**Resolution (Tests: #158, 2026-08-23):** landed as
`tools/muse_assert/test_asserts.py` — 18 tests covering both spec sections:
every assertion kind (must_contain found/absent/naming, register
bounds/violation/note-name round-trip/rest-skip/part-by-name, form
tolerant-empty/notation-backed/missing, tempo_bounds pass/below/above) and
fail-loud behavior (unknown kind rejected, empty assertions no-op, error
carries kind). Real corpus work (Bach BWV227.1) plus synthetic works.

## What to verify

1. **Assertion kinds**
   - must_contain: theme sequence present → pass; absent → fail
   - register: part pitch bounds respected → pass; violated → fail
   - form: section presence (scaffold; may be tolerant)
   - tempo_bounds: tempo map within [min_bpm, max_bpm]
   - unknown kind → AssertionError("unknown-assertion-kind")

2. **Fail-loud behavior**
   - Violations raise AssertionError with kind + detail
   - No silent deviation

## How to run

```bash
python3 -c "from muse_assert import validate_assertions; ..."
```
