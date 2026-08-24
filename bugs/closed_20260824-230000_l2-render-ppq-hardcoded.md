# Bug — L2 renderer hardcodes ppq=480 (#246)

**Filed by:** issue #246 (2026-08-24, surfaced during #243 render-bridge
work; the referenced `bugs/open_20260824-230000_*` file never landed in
the repo — this entry is the record).
**Closed:** 2026-08-24, run=20260824-2254-2185.

## Symptom (from #246)

`tools/muse_render/render.py` `ticks_to_sec` defaulted `ppq=480` and
`render_mockup` never overrode it. Real corpus works use other domains:
mxl-derived works ppq=2 (bwv227.1, Schubert, Beethoven), Byrd MIDIs
ppq=192. bwv227.1 rendered as 0.69s instead of ~47s (240× too fast).

## Resolution

`Mockup` carries `ppq` (additive field, default 480; serialized only when
non-default so existing artifacts are byte-stable) and `render_mockup`
consumes it for every `ticks_to_sec` call. The generate loop's schema v1
has no ppq field — the render bridge sets it from the work at render
time; schema-level ppq remains a possible follow-up (noted in #246).

## Verification

- Regression tests `tools/muse_render/tests/test_render_ppq.py` (6):
  ppq=2 domain renders 152 ticks as 38.5s (the exact bug-report case),
  ppq=192 domain renders 12288 ticks as 32.5s, default-480 behavior
  unchanged, ppq serialization round-trip (implicit when default),
  corpus premise pin (IR reports ppq 2 and 192), bwv227.1-shaped render
  lands in the DoD's 45–75s band.
- muse_render suite: 21 passed; muse_mockup suite: 20 passed; full fast
  gate green.
