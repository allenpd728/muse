# Test spec — L2 performance renderer (task #193)

Written 2026-08-24 by the completing session, per TASK_WORKFLOW §6.

## Status of coverage

6 pytest tests in tools/muse_render/tests/test_render.py, all passing:
- WAV written with 44100 mono, duration matches meta
- Notes/part meta correct
- Tempo map drives rendered duration (fast vs slow differ)
- Determinism: same input → same bytes
- Clip normalization (peak ≤ 32767)
- Empty mockup fails loudly

Run: `cd tools/muse_render && python -m pytest` (<1 s).

## Behaviors still needing coverage (gaps)

1. **sfizz/SFZ samples path.** Primary tier is sfizz; this render path
   is the correct Draw-sine envelope for the test scope, and a future
   instruments per-part (piano vs violin vs voice) array is a separately
   pinning follow-up. When sfizz lands here, golden renders on SSO/VPO
   SPIKE tier map should replace or run alongside.
2. **Balance/gain per part.** part_map carries gain but tests use one
   part only; dynamic contrast across parts over several mockups is a
   must before L3's model comparison.
3. **Anti-aliasing/product-quality sweep.** Sine-envelope output is the
   test scaffold; Sonic-level features (vibrato, breath) belong in the
   L4 distiller domain, not this render path.
4. **Determinism across environments.** Same input renders bytes-equal
   here (within the process); a golden WAV committed per corpus tier
   (small, mid) anchors that.
5. **Per-note tempo_map edge.** notes with onset ahead of the first map
   tick inherit the default 120 bpm; edge-case tests would pin that
   predictable preference, not failing on it.

## Invocation

`cd tools/muse_render && python -m pytest` (<1 s).

## Closed 2026-08-24 (#219, run=20260824-1107-409b)

Landed in tools/muse_render/tests/test_render_gaps.py (9 tests):

- **Gap 2 (per-part gain):** gain scales amplitude; the 0.5/1.0 ratio
  survives linearly below the normalization threshold; string-valued
  part_map entries and orphan parts both fall back to unity gain.
- **Gap 4 (determinism anchors):** fresh Renderer instances are byte-equal
  (no hidden process state); rendering does not mutate the input mockup.
  Golden-WAV-per-corpus-tier remains future work for when the sfizz tier
  lands (a committed golden against the sine scaffold would churn).
- **Gap 5 (before-first-tempo-tick):** onset ahead of the map's first tick
  uses the default 120 bpm — pinned at both the conversion and rendered-
  waveform level; empty/None tempo maps fall back the same way.

Not covered, per the spec's own deferral: gap 1 (sfizz/SFZ primary tier —
no sample libraries wired in) and gap 3 (Sonic-level features belong to
the L4 distiller domain, not this render path).
