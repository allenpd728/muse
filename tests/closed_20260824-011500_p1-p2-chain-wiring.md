# Test spec — P1/P2 chain wiring (issue #201) — CLOSED

The task was itself the integration-test work (wiring the real P1/P2 into
the chain harness's stub stages), so this spec is filed closed: it records
what landed rather than requesting coverage. No recursive `Tests:`
follow-up is filed for a test-layer task.

**Resolution (2026-08-24, run=20260823-2312-h8pk):** muse_chain suite 25
passed (101s); muse_play suite 7 passed (incl. new regression); chain
smoke 4 passed.

## Landed coverage

- **S5→P1 seam** (`tools/muse_chain/chain.py::_stage_decode`): the
  container stage's written `.mu` now stays alive through decode, and the
  real P1 (`muse_decode.decode`) reads it; canonical compare against the
  source Work still gates losslessness. Stage renamed `decode(P1-stub)` →
  `decode(P1)`; the gap-test swap pin now fails if the stage regresses to
  the stand-in.
- **P1→P2 seam** (`_stage_render`): the real P2 (`muse_play.render_work`)
  renders the P1-decoded Work to WAV; verified RIFF header, size > 1000
  bytes, positive duration. Budget-gated at 30k notes (`RENDER_BUDGET_NOTES`)
  so B9 stays SKIP (its buffer would be ≈65 min at 44.1kHz).
- **Chain tests updated**: small works assert all six stages PASS (render
  no longer SKIP); `test_render_skips_over_budget` pins the B9 render
  budget; CLI test asserts ≥6 OK and no SKIP on bwv227.1; tampered-roll
  negative test rebuilt for the container-path signature.
- **P2 bug found by the seam and fixed**: sub-sample-duration note (fast
  tempo, 1-tick duration) crashed the envelope via `env[-0:]` broadcast.
  Guarded in `tools/muse_play/play.py`; regression test
  `test_sub_sample_note_renders` added to the muse_play suite.

## Residual gap (not blocking)

- **S1→P1 golden-vector pin flip**: `tools/s1_stream/tests/test_s1_p1_seam.py`
  still pins `DECODER = roll_decode` (S2 stand-in). Flipping it to the real
  P1 needs a bytes→Work adapter (P1 takes a container path) — small follow-up
  for whoever next touches S1/P1.

## How to run

```bash
cd tools && python -m pytest muse_chain -q          # 25 passed (~101s)
python3 -m pytest muse_chain/test_chain_smoke.py -q # 4 passed (~1s)
./tools/run_tests.sh                                 # fast tier
```
