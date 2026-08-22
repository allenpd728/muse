# Scope — Batch 3: performance layer, interpreter, Player V1

Third buildable layer: the contract between interpretation and audio
(`docs/vision.md` §2, SCHEMA_SPEC.md §7). Node.js throughout, same package as
Batch 1–2 tooling; browser playback for the player. The `.muse.json` schema
defines the space; a **performance document** is one point in it. Both sides —
interpreter and player — validate against the performance schema.

## Decisions (locked)

- **Performance document shape** (`*.muse.perf.json`; the suffix does not
  collide with the harness's `*.muse.json` example glob):
  - `muse_perf_version` — semver, independent of `muse_version`; v0.x may
    break, v1+ additive only (same discipline as §5).
  - `metadata` — `{ source: { schema_id, rendition_id }, interpreter:
    { model, at } }`. Provenance is mandatory here too: which work, which
    rendition, which model produced this performance.
  - **Two clocks, both stored.** Seconds are authoritative for playback
    (Magenta NoteSequence lineage — the player schedules audio in absolute
    time); beats are retained per event and in the tempo map for structural
    traceability — the conformance harness measures motif recall and
    structure fidelity in beat space, so discarding beats would blind the
    metrics that justify the format.
  - `tempo_map: [{ time, beat, bpm }]` — the rendition's tempo decisions
    baked into a curve; the player linearly interpolates between points.
  - `parts: [{ id, name, instrument: { name, program?, sample_set? }, mix?:
    { gain 0-1, pan -1..1, reverb_send 0-1 } }]` — `program` is General MIDI
    0–127 (free tier); `sample_set` names a mid-tier library mapping.
  - `notes: [{ part, pitch, pitch_name, onset, duration, onset_beat,
    duration_beats, velocity, articulation?, controllers? }]` — `pitch` is a
    MIDI note number; `pitch_name` is scientific pitch notation per the
    shared §2.3 grammar. `velocity` 0–127. `articulation` ∈
    `normal|tenuto|staccato|staccatissimo|legato|accent|marcato`. Optional
    per-note `controllers` (pitch_bend, pressure, timbre — MIDI 2.0
    lineage) are forward-compatible: V1 players may ignore them, neural
    renderers consume them.
  - `dynamics?: [{ time, part?, level }]` — curves, level 0–1; `part`
    omitted = global.
  - Reference checks (the #22 "dangling" surfaces): `notes[].part` and
    `dynamics[].part` must resolve against `parts[].id`.
- **Interpreter contract** (`interpreter/expand.mjs`, #23):
  - **Inputs:** the `.muse.json` document, the active rendition (resolved
    from `renditions[]` by id), the performance JSON Schema, and a rendered
    constraint summary (what the validator will check). Model-agnostic:
    API key + model name are config, never hard-coded.
  - **Output:** a performance document. Nothing else — no prose, no partial
    JSON.
  - **The loop:** generate → validate → fix. Validation is two-stage:
    `performance.schema.json` (ajv), then the semantic pass (every
    `constraints.must_contain` motif realized recognizably — motif recall is
    the primary fidelity metric; `register` bounds respected; tempo within
    `globals.tempo.range` unless the rendition overrides). Failures feed back
    as error text; bounded retries (default 3), then fail loudly. A
    performance that can't satisfy the constraints is a bug report, not a
    silent deviation.
  - Provenance: model + timestamp recorded in the performance doc's
    `metadata.interpreter`.
- **Player V1 sound strategy — tiers, not a choice** (`player/render.mjs`,
  #24). All three coexist behind one renderer contract; the decision is
  packaging:
  - **Free tier (reference implementation):** built-in General MIDI
    soundfont, in-browser via Web Audio. Works out of the box; thin sound.
    This is what `npm test` renders and what #24 ships first.
  - **Mid tier:** free orchestral sample sets (Versilian VSCO 2 CE, Soni
    Musicae, Philharmonia) — DAW-mockup quality. Static assets loaded by
    `sample_set`, packaged separately (size, licensing files).
  - **Pro tier:** neural renderer plugin — a model conditioned on the
    performance document (symbolic control → audio; DDSP / neural-codec
    lineage) synthesizes timbre. The performance layer stays canonical; the
    model is a replaceable timbral engine. Honest limitation: multi-instrument
    orchestral realism from symbolic control alone is early-stage;
    single-instrument conditioning is furthest along.
  - **Renderer API contract** (what pro-tier plugins implement):

    ```js
    const renderer = {
      id: "renderer.my-model",           // extensions.<namespace> name
      capabilities: () => ({ streaming: false, controllers: ["pitch_bend"] }),
      render: async (perfDoc, { sampleRate }) => Float32Array[], // per channel
    };
    ```

    Stateless per render; declares controller support so the player can strip
    or keep per-note data; ships its own license record. Open models plug in
    as they mature; no first-party trained model is committed to now.

## Task-list validation (issues #22–#25)

- **#22 performance JSON Schema** — matches the document shape above;
  `schema/performance.schema.json`, referenced from the root. DoD rejection
  cases map to: out-of-range velocity, dangling `notes[].part` ref. No
  conflict.
- **#23 interpreter harness** — matches the interpreter contract; the
  retry-loop DoD is the generate → validate → fix loop above. No conflict.
- **#24 Player V1** — matches; the free tier (GM soundfont) is the reference
  implementation the DoD's audible-fixture test renders against. Browser +
  WAV-file output both required. No conflict.
- **#25 end-to-end demo** — matches; the two-rendition audible difference is
  exactly what the rendition presets + interpreter nondeterminism produce.
  Note the dependency chain: #25 needs #23 and #24 done, not merely written.

No task needs re-scoping.

## Consequences for spec work

- SCHEMA_SPEC.md §7 is no longer "planned" — the performance document shape
  above is drafted there as **draft v0** (marked unstable; additive discipline
  starts at v1 like everything else).
- The schema's `constraints` become *checkable* in Batch 3 for the first
  time: motif recall and register/tempo bounds get executable semantics in
  the interpreter's validation loop. If that pass surfaces ambiguity in
  §2.5's prose (e.g. what "recognizably" means numerically), that is a spec
  amendment, not an interpreter-side workaround.
- `pitch_name` in the performance document reuses the §2.3 pitch grammar —
  one pitch language across schema, importer IR, and performance layer.
