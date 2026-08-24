# Test spec — CI conformance gate

**Task:** #163 (CI conformance gate)
**Written:** 2026-08-24

## What to verify

1. **Gate command**
   - `./tools/run_tests.sh` on all suites: ir, corpus_loader, muse_diff,
     muse_ops, muse_unpack, muse_assert, muse_seed, muse_seed_cli,
     muse_author, s1_stream, muse_viz, muse_roll, assertions, chain_smoke,
     muse_explorer, muse_probes (16 fast, exit 0)
   - `./tools/run_tests.sh --full` adds muse_analyze + muse_chain + qa_frontend
     (slow, allow-fail)

2. **Schema**
   - yaml parses (.yml syntax)

3. **Files**
   - `.github/workflows/conformance.yml`
   - `tools/run_tests.sh`

## How to run locally

```bash
./tools/run_tests.sh          # fast tier (exit 0 = CI pass)
./tools/run_tests.sh --full   # 19 suites incl. slow (allow-fail)
```

