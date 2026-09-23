# Tier 2 test baseline — pre-rename

Captured immediately before the first Tier 2 identifier rename (rubato #332).
Runner: `tools/run_tests.sh --full`. Any suite that is red here is out of scope
for the rename and must be recorded as known-failing.

- Repo: `philipdallen/rubato`
- Branch: `main`
- Commit: `48dbd2a9964386f50e12c66d68d9c34e90ea7d33` (2026-09-23 06:24:43 +0000)
- Captured: 2026-09-23 (run=20260923-0821-ieob)
- Aggregate result: all suites green

## Suite results

```
PASS  ir                 53s    131 passed in 52.31s
PASS  corpus_loader      69s    16 passed in 68.62s (0:01:08)
PASS  muse_diff           2s    21 passed in 1.26s
PASS  muse_ops            1s    22 passed, 1 skipped in 0.04s
PASS  muse_unpack         0s    52 passed, 1 warning in 0.12s
PASS  muse_assert         1s    23 passed in 0.09s
PASS  muse_seed           5s    155 passed, 1 skipped in 4.97s
PASS  muse_seed_cli       3s    14 passed in 3.02s
PASS  muse_author         1s    9 passed in 0.83s
PASS  s1_stream          35s    45 passed in 35.58s
PASS  muse_viz           59s    12 passed in 54.05s
PASS  muse_roll          63s    60 passed in 62.54s (0:01:02)
PASS  assertions          2s    14 passed in 1.91s
PASS  chain_smoke         2s    4 passed in 1.67s
PASS  muse_explorer      89s    12 passed in 87.87s (0:01:27)
PASS  muse_probes         1s    36 passed in 1.47s
PASS  muse_lineage        1s    12 passed in 0.62s
PASS  muse_mockup         4s    27 passed in 3.64s
PASS  muse_provider       1s    11 passed in 0.15s
PASS  muse_generate       0s    10 passed in 0.16s
PASS  muse_grow           2s    21 passed in 1.51s
PASS  muse_decode         1s    18 passed, 1 warning in 0.25s
PASS  muse_play           2s    10 passed in 1.04s
PASS  muse_render         1s    27 passed in 0.64s
PASS  muse_compare        1s    19 passed in 0.41s
PASS  muse_distill        0s    9 passed in 0.17s
PASS  muse_mockup         4s    27 passed in 3.30s
PASS  muse_workbench_runner   14s    42 passed in 14.36s
PASS  muse_budgets        0s    9 passed in 0.07s
PASS  muse_event          1s    7 passed in 0.04s
PASS  docs                0s    18 passed in 0.13s
PASS  muse_docs           1s    78 passed in 0.45s
PASS  hub_sweep           0s    25 passed in 0.08s
PASS  auditor             2s    48 passed, 1 warning in 1.12s
PASS  muse_form           0s    5 passed in 0.08s
PASS  muse_audio          1s    11 passed in 0.95s
PASS  muse_analyze      141s    23 passed in 139.90s (0:02:19)
PASS  muse_chain         96s    26 passed in 94.97s (0:01:34)
PASS  qa_frontend       175s    176 passed in 174.75s (0:02:54)
all suites green
```
