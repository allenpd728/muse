# Test spec — P2 reference renderer (task #198)

Written 2026-08-24 by the completing session, per TASK_WORKFLOW §6.

## Status of coverage

6 pytest tests in tools/muse_play/tests/test_play.py, all passing:
- WAV write from BWV227 (279 notes, 4 parts)
- Wrapper defaults output
- Determininism (same source → same bytes)
- MIDI source renders (Byrd, 71 notes)
- Only-rests work fails loudly
- Empty parts Work raises

Run: `cd tools/muse_play && python -m pytest` (~0.25 s).

## Behaviors still needing coverage (gaps)

1. **`.mu` container input.** P3's `.mu` decode gate if it exists; the CLI's
   stated format list (.xml/.mxl/.mid) should match P1's acceptance.
2. **Package import laziness.** The lazy-IR-import pattern used in
   tools/muse_play/play.py `@TASK_WORKFLOW` is documented — when other
   tools add it, a move-to-common helper is the cleanup.
3. **Sample-tier quality.** The render envelope is the same fallback
   L2's clean test path uses; the true soundfont option lives in L2
   tools/muse_render. Renders here use the general fallback, not the
   SPIKE's SSO/VPO tier.

## Invocation

`cd tools/muse_play && python -m pytest` (~0.25 s).
