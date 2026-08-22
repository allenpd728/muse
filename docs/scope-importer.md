# Scope — Importer (MIDI/MusicXML → `.muse.json`)

Second buildable layer: import existing symbolic music into Muse schemas.
Node.js throughout, same package as the Batch 1 tooling. Per SCHEMA_SPEC.md §4
imports are **lossy by design**: they produce `material` + `globals` + a
first-pass `form` + one default rendition. The importer's job is a faithful,
validating starting point — not a finished composition. Cleanup is
agent-assisted authoring, downstream of import.

## Decisions (locked)

- **MIDI parsing:** `@tonejs/midi`. Established, pure JS, and parses exactly
  the IR inputs we need out of the box: tempo map, time-signature map, key
  signatures, and per-track notes with tick and second timings. Lower-level
  alternatives (`midi-file`) make us reimplement meta-event handling for no
  gain.
- **MusicXML parsing:** `musicxml-interfaces` + `fflate`.
  `musicxml-interfaces` is a complete, typed MusicXML 4.0 model with a
  pure-JS parser — no native deps, full element coverage (harmony, directions,
  part linkage) that lighter SAX scrapers miss. `.mxl` is a zip container;
  `fflate` decompresses it without pulling in a heavier unzip dependency.
- **IR canonical time unit: beats** (quarter notes), matching the schema —
  `material.motifs[].durations` and rhythm grids are in beats. Parsers convert
  source ticks/divisions to beats at the IR boundary; nothing downstream of
  the IR sees ticks or seconds.
- **IR pitch representation: MIDI note number internally**, emitted as
  scientific pitch notation (`D4`, middle C = C4) in schema output, matching
  the spec's pitch grammar (`material.motifs[].pitches`,
  `constraints.register` bounds). MusicXML spelling (step/alter/octave) is
  kept on the IR note as optional metadata so synthesis can prefer the
  composer's spelling over a computed one.
- **IR shape** (what both parsers emit, what synthesis consumes):
  - `tempoMap: [{ beat, bpm }]`, `meterMap: [{ beat, beats, unit }]`,
    `keyMap: [{ beat, tonic, mode }]` — maps, not scalars; MIDI and MusicXML
    both change these mid-piece.
  - `parts: [{ id, name, program?, notes: [{ midi, spelling?, onsetBeat,
    durationBeats, velocity? }] }]` — one IR part per MIDI track / MusicXML
    `score-part`.
- **Lossy-mapping policy** (what is dropped, and where it goes):
  - *Kept:* pitches, onsets, durations, tempo/meter/key maps, part structure.
  - *Flattened:* `globals.tempo.bpm` = opening tempo; `tempo.range` =
    observed [min, max] across the tempo map when it varies, omitted when
    constant. `globals.meter`/`key` = opening values; mid-piece changes are
    dropped from `globals` (spec v0 has no per-section meter/key overrides —
    noted as a spec gap, not worked around).
  - *Dropped:* engraving/layout, voice leading within chords, articulation,
    dynamics/velocity shaping, pedaling. Velocity is retained on IR notes
    (cheap, may inform rhythm-cell extraction) but does not reach the schema.
  - Every import records the drop in `metadata.provenance` (one entry:
    `event: "import"`, source filename/format, `ai: false`).
- **Inferred vs. left for cleanup** — the one open design question from
  issue #19 (motif extraction) is settled as *heuristic, marked, never
  silent*:
  - *Inferred by heuristic:* repeated pitch-rhythm interval patterns
    (length ≥ 3 notes, occurring ≥ 2×, transposition counts as a recurrence)
    become `material.motifs`; exact repeated rhythmic grids become
    `material.rhythms`; repeated multi-bar blocks become `form.sections` with
    `order`/`repetition` derived from recurrence.
  - *Left for agent/human cleanup:* section `role` (default `"custom"`),
    `theme` assembly from motifs, `harmony.progressions` (MusicXML harmony
    elements are imported when present; chord inference from note simultaneity
    is **not** attempted — simultaneity stacks are not progressions),
    `constraints`, additional renditions.
  - *Marking:* every heuristic inference is listed in
    `extensions.importer.inferred` (field path + reason). Extensions are the
    spec-sanctioned namespace for this (§2.7); conforming tools ignore the
    namespace, cleanup agents read it. Nothing is silently guessed (issue #19
    definition of done).
- **Default rendition:** exactly one, id `r.default`, name `"Default"`,
  `params.tempo_bpm` = `globals.tempo.bpm`, instrumentation from part
  names/programs. `style` is omitted — an import has no genre treatment, and
  inventing one would violate the no-silent-guessing rule.
- **CLI:** `node importer/cli.mjs <file.mid|file.musicxml|file.mxl> -o
  out.muse.json`; format detected by extension + magic bytes. Output is
  validated against `schema/muse.schema.json` before writing — the importer
  never emits a non-validating document.

## Task-list validation (issues #16–#20)

- **#16 IR** — matches the IR shape above; `importer/ir.mjs` is the right
  home. "Round-trips a hand-built fixture losslessly" covers the
  beats/pitch conventions above.
- **#17 MIDI parser** — library settled (`@tonejs/midi`); fixture-driven as
  specified. No conflict.
- **#18 MusicXML parser** — library settled (`musicxml-interfaces` +
  `fflate`); the public-domain chorale fixture doubles as the first corpus
  entry for #20.
- **#19 Synthesis** — the motif-extraction open question is resolved above
  (heuristic + `extensions.importer.inferred` marking). Chord inference is
  explicitly out of scope; the issue's "uncertain inferences are marked"
  requirement is satisfied by the marking mechanism.
- **#20 Corpus + CLI** — Bach chorales align with the vision doc's benchmark
  corpus strategy (public-domain scores as canonical files). CLI shape
  settled above. CI hooks into the existing `npm test` workflow.

No task needs re-scoping; #16 can start as soon as this doc lands.

## Consequences for spec work

Two spec gaps surfaced (neither blocks the batch):

- No per-section meter/key overrides in v0 — mid-piece changes are dropped
  from `globals`. Candidate for v0.x spec amendment.
- No first-class "needs review" marker — `extensions.importer.inferred` is
  the workaround; if cleanup agents become primary consumers, a typed field
  may be worth spec'ing.

Both are noted here rather than filed as blockers: they are design
*choices* for a future spec edit, not missing information that stalls work.
