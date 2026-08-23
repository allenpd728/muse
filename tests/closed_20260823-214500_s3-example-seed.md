# Test spec — S3.6 example seed — CLOSED

**Task:** #147 (S3.6 — Example seed)
**Written:** 2026-08-23

**Resolution (Tests: #159, 2026-08-23):** landed as
`tools/muse_seed/test_example_seed.py` — 10 tests covering both spec
sections: seed validity (loads, validate_seed passes, AI disclosure
present, philosophy block valid) and self-validation (own assertions pass
against the source work, register pin P4 F2..C4 within C2..C4, tempo
bounds pin, sanctioned tempo range covers the notated 96 bpm), plus
YAML/JSON round-trips. Package: 125 passed, 1 skipped.

## What to verify

1. **Seed validity**
   - seeds/bwv227.1.seed.yaml loads via load_seed
   - validate_seed passes (required keys, types)
   - Assertions validate against corpus/bach/bwv227.1.mxl (register + tempo_bounds)

2. **Self-validation**
   - The example seed's own assertions pass against its source work
   - dump_seed round-trips (YAML → load → identical)

## How to run

```bash
python3 -c "from muse_seed import load_seed, validate_seed; from muse_assert import validate_assertions; ..."
```
