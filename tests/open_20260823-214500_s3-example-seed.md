# Test spec — S3.6 example seed

**Task:** #147 (S3.6 — Example seed)
**Written:** 2026-08-23

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
