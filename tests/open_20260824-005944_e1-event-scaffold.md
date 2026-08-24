# Test spec — E1 event scaffold (task #200)

Written 2026-08-24 by the completing session, per TASK_WORKFLOW §6.

## Status of coverage

4 pytest tests in tools/muse_event/tests/test_event.py, all passing:
- Ladder covers all five corpus works in order
- event_chain executes per rung (Bach rung 1)
- run_ladder writes event-ledger.json, 5/5 rungs ok
- Ledger shape (work_id, rung pinned)

Run: `cd tools/muse_event && python -m pytest` (<1 s).

## Behaviors still needing coverage (gaps)

1. **Chain steps' implementation.** The chain names author → mockup →
   assert → render, but only names the process — the actual stage calls
   ab sub-configs per tooling path (muse_author CLI, mockup harness,
   muse_assert gate, muse_render render). Once the chain's invocation
   is chosen (CLI or in-process API), the tests pin invocation-contract
   explicitly.
2. **Missing-corpus-partial-failures.** Ladder runs assumes the corpus
   is present; missing files raise at chain start (correct), but no
   graceful `found_working=False` per rung with details.
3. **Era-throughput relationship.** era="classical" is passthrough today;
   when era budgets differ it must be tested that the mockup/changes
   reflect it.
4. **Ledger is flush-on-start.** Write-on-success, not incremental
   (live-progress); the pipeline is not idle-time save unless it becomes.

## Invocation

`cd tools/muse_event && python -m pytest` (<1 s).
