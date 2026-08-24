# Bug — unified runner doesn't run the newest tools' suites

**Found:** 2026-08-24, run=20260823-2312-h8pk, gathering gate evidence for #201.
**Disposition:** filed #202 (`status:available`).

## Symptom

`tools/run_tests.sh` (the repo's one-command gate) omits every tool that
landed after the runner's suite list was last extended:

| Suite | Tests | Registered? |
|---|---|---|
| muse_play (P2) | 7 | no |
| muse_render (L2) | yes | no |
| muse_compare (L3) | yes | no |
| muse_distill (L4) | yes | no |
| muse_mockup (L1) | yes | no |
| muse_decode (P1) | **none exist** | no |

So "all suites green" currently means 16 suites / 509 tests — and none of
the P1/P2/L-series tools are in it. P1 (#197) shipped with a test spec
(`tests/open_20260824-020000_p1-decoder.md`) but no test files and no open
Tests: issue.

## Root cause

The runner discovers suites by explicit registration (deliberate — keeps
spike/ and __pycache__ out), which makes registration a manual step no
task's DoD currently enforces. Five consecutive tasks skipped it.

## Fix

Register the existing suites (fast tier where cheap); write P1's tests per
the open spec and register `muse_decode`. Details in #202.

## Impact

Chain smoke covers P1/P2 indirectly post-#201, so the pipeline isn't
ungated — but per-tool regressions in five packages would only surface via
direct pytest invocation, which nobody runs.
