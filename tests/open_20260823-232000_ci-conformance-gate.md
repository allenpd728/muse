# Test spec — CI conformance gate

**Task:** #163 (CI conformance gate)
**Written:** 2026-08-23

## What to verify

1. **Gate command**
   - `./tools/run_tests.sh` on all suites: ir, corpus_loader, muse_diff,
     muse_ops, muse_unpack, muse_assert, muse_seed, muse_seed_cli,
     muse_author, s1_stream, muse_viz, muse_roll, chain_smoke, muse_explorer
     (12 fast, exit 0)
   - `./tools/run_tests.sh --full` adds muse_analyze (13 incl. Beethoven 9,
     allow-fail)

2. **Schema**
   - yaml parses (.yml syntax)

3. **Files**
   - `.github/workflows/conformance.yml`

## How to run locally

```bash
./tools/run_tests.sh          # fast tier (exit 0 = CI pass)
./tools/run_tests.sh --full   # 13 suites incl. B9 (allow-fail)
```
