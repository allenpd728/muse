# Test spec — S3.1 container & encoding

**Task:** #142 (S3.1 — Container & encoding)
**Written:** 2026-08-23

## What to verify

1. **Schema validation**
   - Missing required keys → SeedError (format_version, work_id, params, assertions)
   - Unknown top-level keys → SeedError
   - params/assertions must be mappings; variation_points must be a list

2. **Round-trip**
   - YAML dump → YAML load: identical dict
   - JSON dump → JSON load: identical dict (byte-fair for machine use)

3. **Example seed**
   - Bach BWV227.1 seed loads; assertions/params round-trip

## How to run

```bash
python3 -c "from muse_seed import Seed, load_seed, dump_seed, validate_seed; ..."
```
