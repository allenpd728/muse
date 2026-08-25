# Bug — muse_audio schema-path bridge drops the work's ppq (#246 seam)

**Found:** 2026-08-25, run=20260825-1033-cae1, reviewing whether #246's
ppq fix actually propagated to all mockup constructors.

## Symptom

`tools/muse_audio/audio.py::_schema_dict_to_mockup` — the real L1
generate loop's wire-format → Mockup bridge — built `Mockup(...)` without
setting `ppq`, so mockups from the real generate path carried the 480
default regardless of the work's tick domain. bwv227.1 is ppq=2: any
render through this path played 240× too fast (same damage #246 fixed in
the renderer, surviving through this call site). Verified live: a
bridge-path mockup rendered 0.503s of audio vs 1.125s with the correct
domain on a single-note probe; full works scale accordingly.

The stand-in constructor path (line ~155) set `mockup.ppq = work.meta.ppq`
correctly — only the schema-v1 dict path missed it.

## Fix

`mockup.ppq = getattr(getattr(work, "meta", None), "ppq", 480)` in
`_schema_dict_to_mockup`.

## Verification

`tools/muse_audio/tests/test_audio.py::TestSchemaDictToMockup::
test_ppq_carried_from_work` — bridge output ppq equals the work's
`meta.ppq` (2 for bwv227.1).

## Lesson

#246 fixed the consumer (renderer); the producers each needed the field
set. A constructor-level sweep (`Mockup(` call sites) is the right
follow-through whenever a new domain-carrying field lands.
