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

---

## Closed 2026-08-24 (issue #225, run=20260824-1059-b671)

Gap 1 landed as a wire + 3 tests: with P3's vector store committed, the
CLI now accepts `.mu` (decoded via P1's muse_decode — the seam the CLI
docstring reserved), matching P1's acceptance:

- **CLI end-to-end** — `python -m muse_play <p3-vector.mu>` renders WAV
  (BWV227.1: 279 notes, 4 parts pinned).
- **Container ≡ source byte-equivalence** — the `.mu` vector and its
  corpus MusicXML render to identical WAV bytes; the S1 contract holds
  through both input paths.
- **Loud rejection kept** — truly unsupported suffixes still exit 2.

`tools/muse_play/__main__.py` gained a `_load_source` seam (lazy
muse_decode import, mirroring the module's lazy-IR pattern); README
format list updated. Gaps 2–3 stand by design (lazy-import cleanup is a
common-helper decision; sample-tier quality is L2's scope).

Gate: `cd tools/muse_play && python -m pytest` → 10 passed (~0.7 s);
`./tools/run_tests.sh` fast tier → all suites green.
