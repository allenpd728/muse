# Test spec — E2E chain harness (issue #162)

Written by the completing agent per TASK_WORKFLOW step 6. The harness
landed with 10 tests (`cd tools/muse_chain && python -m pytest`, ~83s —
the B9 chain run dominates).

## Landed coverage (tools/muse_chain/test_chain.py)

- **Composition:** two small works green through all six stages (render
  SKIPped as the P2 stub); artifacts present and well-formed (MUR1 magic,
  manifest JSON).
- **B9 budget:** verify(W4) SKIPped over 30k notes while decode's
  structural check PASSes — the losslessness proof path for large works.
- **Failure isolation:** a missing file fails exactly one stage, named
  `parse(W1)`; every stage name carries its task noun.
- **Determinism:** two full runs (small registry) produce identical
  artifacts; pack is byte-deterministic.
- **CLI:** single-work exit 0; --determinism exit 0.
- **Report:** docs/chain-report.md committed (full registry, determinism
  PASS).

## Gaps for a `Tests:` follow-up

1. **P1/P2 stage swap.** When the sandboxed decoder lands, the chain's
   decode stage must run it instead of the S2 stand-in — pin the swap
   with a test that asserts the stage name changes from P1-stub to P1.
2. **Renderer stage.** Same for P2: WAV output sanity (non-empty, valid
   RIFF header) once the renderer exists.
3. **Report freshness tripwire.** docs/chain-report.md is a committed
   artifact; a CI check that re-runs --all and diffs the report belongs
   to the CI conformance gate (#163).
4. **Negative stage injection.** Only parse-failure is pinned; pack and
   container failure paths (corrupting inputs mid-chain) need fixtures
   that don't exist yet (a deliberately unencodable work).

## How to run

```bash
python3 tools/muse_chain/cli.py --all
cd tools/muse_chain && python -m pytest
```
