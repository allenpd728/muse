# Test spec — #91: offline fallback realization (bare motif pool)

**Source task:** #91 (offline interpreter: realize sections from bare motif
pool when no uses/themes)
**Code under test:** `interpreter/offline.mjs` fallback paths.

DoD coverage landed with the task: `tests/play.test.mjs` — 7 new checks
(all 6 chorales render >0 notes, bwv269 note-count band, full example
fallback-never-fires pin via the existing realization checks). This spec
is for what remains.

## Behaviors to verify

- **Form-less vs section-less:** two distinct fallback levels landed
  (section-without-uses → motif pool; document-without-form → default
  section). Pin each separately with a minimal synthetic doc (current
  checks exercise corpus files, which mix the two).
- **Fallback vs harmony bed interaction:** a section with no uses AND no
  harmony — lead only, no bed; corpus entries have no progressions, so
  the bed never fires there (pin: notes[].part are all p.lead).
- **Octave policy:** fallback plays at notated pitch (imports are the
  composer's voicing); uses-driven realization transposes +12. A doc
  mixing a uses-section and a fallback-section pins both behaviors.
- **Repetition of the default section:** form-less docs synthesize
  section.default with bars 32 — pin that a doc declaring repetition for
  a real section never gets the synthetic default.
- **Tempo-shape realization in fallback sections:** tempo_shapes keyed to
  a real section id works; keyed to a fallback id (section.default) is
  undefined behavior — decide and pin.
- **WAV smoke:** corpus chorale renders through tools/play.mjs to a
  non-silent WAV (the play CLI test pattern, one chorale).

## How to run

`npm test`; new cases into `tests/play.test.mjs`.
