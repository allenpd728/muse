# Test spec — CI conformance gate

**Task:** #163 (CI conformance gate)
**Written:** 2026-08-23

## What to verify

1. **Gate command**
   - `MUSE_SKIP_SLOW=1 python3 -m pytest tools/…` on all suites: i/r/ir,
     corpus_loader, muse_diff, muse_analyze, muse_viz, muse_seed,
     muse_assert, muse_author, muse_seed_cli, muse_ops, s1_stream, muse_mu
   - Slow profile: muse_analyze (full) for Beethoven 9 budget, allow-fail

2. **Schema**
   - yaml parses (.yml syntax)

3. **Files**
   - `.github/workflows/conformance.yml`

## How to run locally

```bash
MUSE_SKIP_SLOW=1 python3 -m pytest tools/…   # matches CI behavior
```
