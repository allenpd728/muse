# Test spec — chain smoke (#169) — CLOSED

Written by the completing agent per TASK_WORKFLOW step 6. The chain smoke
test is the fast-tier integration gate: `tools/muse_chain/test_chain_smoke.py`
(4 tests, ~0.3s) — three small-registry works green through
parse→pack→container→decode with W4 verify PASS, plus determinism.

**Resolution (Tests: #172, 2026-08-23):** all three gaps closed —
`tools/muse_chain/test_smoke_gaps.py` (4 tests): registry scope pinned
(Bach mvt 1 + Byrd Kyrie/Gloria), smoke-registry-is-fast timebox (<30s for
two determinism runs), failure-injection drill (single named FAIL stage),
runner hookup (--list shows chain_smoke + slow tier heading).

## Landed coverage

- **Integration:** each fast-registry work runs the full chain; W4 verify
  must PASS (not just "no FAIL").
- **Determinism:** two runs → identical artifacts on the fast registry.
- **Runner wiring:** registered as `chain_smoke` in the fast tier of
  `tools/run_tests.sh` (list output pinned above).

## Gaps for a `Tests:` follow-up

1. **Registry scope.** The fast registry is Bach mvt 1 + Byrd Kyrie/Gloria
   (~0.3s). Once P1 lands, decide whether the smoke registry grows (per-tier
   representative) or stays minimal.
2. **Failure-injection smoke.** Only green paths are under the smoke gate;
   a failing-stage drill (same spirit as test_chain.py's isolation tests)
   would pin the runner's report format end-to-end.
3. **Slow registry.** The full 13-file chain stays in `test_chain.py`
   (~83s, dominated by B9); a --full tier hookup in run_tests.sh is
   pending the W6 budget discussion.

## How to run

```bash
python3 -m pytest tools/muse_chain/test_chain_smoke.py -q
./tools/run_tests.sh --list
```
