# Bug — L2 renderer hardcodes ppq=480 (real works render at wrong speed)

**Found:** 2026-08-24, run=20260824-1032-xjzf, rendering seed-revision
audio for #243. Issue: #246.
**Disposition:** fixed in the #243 commit (mockup carries ppq; render
uses it) — see the closed entry's commit reference.

## Symptom

`tools/muse_render/render.py` `ticks_to_sec(tick, tempo_map, ppq=480)` is
called by `render_mockup` without a ppq argument. Corpus works are not
ppq=480: mxl-derived works parse to ppq=2 (bwv227.1, schubert, beethoven),
Byrd MIDIs to ppq=192. bwv227.1 renders as 0.689s of audio instead of
~47s (240× too fast); Byrd renders 2.5× too fast.

## Repro

```bash
python3 tools/muse_audio/cli.py corpus/bach/bwv227.1.mxl \
    --seed seeds/bwv227.1.v1.seed.yaml --label v1
# → bwv227.1.v1.wav, 0.689s (should be ~47s at the seed's 62..129 bpm arch)
```

## Root cause

The Mockup model has no ppq field, so the renderer assumes the MIDI
standard 480. The chain harness renders via muse_play (P2 handles ppq
correctly) and muse_render's own tests use synthetic tick domains, so no
suite exercised a real work's tick resolution through L2.

## Fix (landed with #243)

`Mockup.ppq: int = 480` (additive, backwards-compatible default), carried
through dump/load; `render_mockup` passes `mockup.ppq` to `ticks_to_sec`;
the render bridge (muse_audio) sets it from `work.meta.ppq`. The L1
generate loop's schema v1 has no ppq field — mockups from the LLM are in
the work's tick domain, so the bridge stamps ppq at render time;
schema-level ppq is a possible follow-up.
