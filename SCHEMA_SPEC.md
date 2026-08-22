# Muse Schema Specification — v0 (Draft)

**Status:** Draft. Normative language and validation rules will tighten in later versions.
**Goal:** Define a JSON-native document that captures a musical composition as a *space of valid renditions* rather than a single fixed performance — the difference between a score and a score plus its orchestration rules.

A Muse schema document answers two questions:

1. **What is the composition?** — themes, motifs, rhythms, harmony, form, and the constraints that make it *this* piece and not another.
2. **What may vary?** — the sanctioned degrees of freedom (tempo range, instrumentation, genre treatment, density, energy) that a rendition may explore while remaining a rendition of the same work.

## 1. Design goals

- **JSON-native.** Web-friendly, diffable, schema-validatable, LLM-legible. Prior art: JAMS (annotations), MEI (semantic rigor), MusicXML (interchange — Muse schemas must round-trip import from MusicXML/MIDI where possible).
- **Semantics over engraving.** The schema describes musical *intent* (motif, theme, variation, function of a section), not visual layout. It is closer to MEI's philosophy than MusicXML's.
- **Two-population authoring.** Hand-authorable by a composer in a node-based editor, and generatable/editable by an agent from natural-language direction.
- **Engine-agnostic.** Any conforming generative engine must be able to render any conforming schema. Rendering fidelity is measured against the schema's constraints, not against a reference recording.
- **Rights-carrying.** Provenance, authorship, and licensing terms travel inside the document.

## 2. Document structure

A Muse schema is a single JSON object with these top-level members:

```jsonc
{
  "muse_version": "0.1",          // schema spec version (required)
  "metadata":    { },             // title, composer, provenance, license (required)
  "globals":     { },             // tempo, meter, key, tuning (required)
  "material":    { },             // themes, motifs, rhythm cells, harmonic vocabulary
  "form":        { },             // ordered sections, their roles, and how material appears in them
  "constraints": { },             // invariants every rendition must satisfy
  "renditions":  [ ],             // sanctioned rendition presets ("genre covers")
  "extensions":  { }              // namespaced, engine- or composer-specific data
}
```

### 2.1 `metadata`

```jsonc
"metadata": {
  "id": "muse:work:01J…",              // stable work identifier (ULID/UUID)
  "title": "…",
  "composer": { "name": "…", "id": "…" },
  "created": "2026-08-21T00:00:00Z",
  "license": {                          // what a renderer/distributor may do
    "renditions": "presets-only",       // presets-only | open-within-constraints | closed
    "attribution": "required",
    "commercial": true
  },
  "provenance": [ ]                     // generation/edit history; AI involvement disclosures
}
```

### 2.2 `globals`

```jsonc
"globals": {
  "tempo":  { "bpm": 96, "range": [84, 112], "feel": "straight" },
  "meter":  { "beats": 4, "unit": 4 },          // additive/odd meters allowed: { "beats": [3,3,2], "unit": 8 }
  "key":    { "tonic": "D", "mode": "dorian" }, // or "atonal", or per-section overrides
  "duration_bars": 64
}
```

Ranges, not scalars, are the point: `tempo.range` defines what renditions may explore; `constraints` (§2.5) can narrow it further per section.

### 2.3 `material` — themes, motifs, rhythm cells

The reusable musical vocabulary of the work. Everything in `form` references material by ID.

```jsonc
"material": {
  "motifs": [
    {
      "id": "motif.a",
      "kind": "pitch_rhythm",             // pitch | rhythm | pitch_rhythm | timbre | harmonic
      "pitches":   [ "D4", "F4", "A4", "G4" ],
      "durations": [ 0.5, 0.5, 1.0, 1.0 ],  // in beats
      "contour":   "up-up-down",
      "tags":      [ "primary", "opening" ]
    }
  ],
  "themes": [
    {
      "id": "theme.1",
      "phrases": [ { "motifs": [ "motif.a", "motif.a#seq(+2)" ] } ],  // motifs with transforms
      "cadence": "half"
    }
  ],
  "rhythms": [
    { "id": "groove.1", "pattern": [1, 0, 0.75, 0, 1, 0, 0.75, 0.25], "grid": "8n" }
  ],
  "harmony": {
    "progressions": [
      { "id": "prog.verse", "chords": [ "Dm7", "G7", "Cmaj7", "Am7" ], "bars_per_chord": 1 }
    ],
    "vocabulary": "diatonic-plus-bVII"     // free-text or formal grammar ref
  }
}
```

**Transforms** are suffix expressions applied at the reference site: `motif.a#seq(+2)` (sequence up a step), `#inv` (inversion), `#retro` (retrograde), `#aug(2)` (augmentation), `#dim(0.5)` (diminution). The transform set is the mechanism for **variations** — a core primitive, not an afterthought.

### 2.4 `form` — sections and structure

```jsonc
"form": {
  "sections": [
    {
      "id": "verse.1",
      "role": "verse",                    // intro | verse | pre_chorus | chorus | bridge | solo | outro | custom
      "bars": 16,
      "uses": [ { "ref": "theme.1", "variation": "plain" } ],
      "harmony": "prog.verse",
      "energy": 0.4                       // 0–1 target, interpreted per-rendition
    },
    {
      "id": "chorus.1",
      "role": "chorus",
      "bars": 8,
      "uses": [ { "ref": "theme.1", "variation": "developed#aug(2)+orn" } ],
      "energy": 0.9
    }
  ],
  "order": [ "verse.1", "chorus.1", "verse.1", "chorus.1" ],
  "repetition": { "verse.1": { "min": 2, "max": 4 } }
}
```

`order` and `repetition` allow the form itself to be a bounded space (e.g., verse count may vary 2–4× across renditions) rather than a fixed sequence.

### 2.5 `constraints` — the invariants

What every rendition must satisfy to be a rendition of *this* work. Constraints are the conformance contract between composer and engine.

```jsonc
"constraints": {
  "must_contain": [ "motif.a" ],                       // motif recall requirement
  "must_not":      [ { "kind": "modulation_beyond", "semitones": 3 } ],
  "tempo_lock":    { "chorus.1": [ 92, 104 ] },
  "register":      { "theme.1": [ "C4", "A5" ] },
  "structure":     { "form_deviation": "none" }        // none | reorder | abridge
}
```

A conforming engine renders audio that satisfies all `constraints` while exploring the freedom left by `globals` ranges and the active `rendition`.

### 2.6 `renditions` — sanctioned presets ("genre covers")

Named parameter bundles a listener can select. Each rendition is a first-class object with its own metadata (so it can be credited, licensed, and traded separately).

```jsonc
"renditions": [
  {
    "id": "r.synthwave",
    "name": "Midnight Drive",
    "style": { "genre": "synthwave", "era": "1984", "references": [ "arpeggiated bass", "gated reverb drums" ] },
    "params": { "tempo_bpm": 100, "instrumentation": [ "analog synth", "drum machine" ], "density": 0.7, "swing": 0.0 },
    "author": { "name": "…" }            // may differ from composer — renditions are collaborative works
  },
  {
    "id": "r.quartet",
    "name": "Late Set",
    "style": { "genre": "jazz quartet", "era": "1959" },
    "params": { "tempo_bpm": 88, "instrumentation": [ "piano", "upright bass", "brushes", "tenor sax" ], "swing": 0.62 }
  }
]
```

**Hard rule:** `style.references` describe styles, eras, and production techniques. Named-artist imitation ("sounds like <artist>") is out of spec without an attached license record (see §2.1 `license`).

### 2.7 `extensions`

Namespaced escape hatch, e.g. `"extensions": { "engine.audiocraft": { "cfg": 3.5 } }`. Conforming engines must ignore unknown namespaces, never fail on them.

## 3. Conformance

A renderer is **Muse-conforming** if it:

1. Produces audio satisfying every entry in `constraints`.
2. Realizes every `must_contain` motif recognizably (motif recall is the primary fidelity metric).
3. Follows `form.order` within the bounds of `repetition` and `structure.form_deviation`.
4. Stays within `globals` ranges unless the active rendition explicitly overrides them.

**Validation (planned):** a JSON Schema for syntactic validation, plus an engine-side test harness reporting motif-recall and structure-fidelity scores per render.

## 4. Interchange

- **Import:** MusicXML and MIDI (lossy: imports produce `material` + a single default rendition; form/roles inferred where possible).
- **Export:** flattened, fixed renderings may export to MusicXML/MIDI; the schema itself is never "compiled away" — it remains the canonical artifact.

## 5. Versioning

`muse_version` is semver. v0.x drafts may break compatibility freely; from v1.0, all changes are additive within a major version.

## 6. Open questions for v0.x

- How formal should `harmony.vocabulary` grammars be (regex-like chord grammar vs. free text + reference progressions)?
- Representation of microtonality/tuning systems beyond 12-TET.
- Whether `constraints` should support engine-checkable predicates (e.g., "chorus must be ≥ +6 dB denser than verse") as a typed DSL.
- Minimal motif encoding for non-pitched / timbral material.

## 7. Performance layer (planned)

A companion spec will define the **performance document**: the concrete event
format an interpreter produces from a schema + rendition and a player renders
to audio. Expressive-MIDI-as-JSON: note events with pitch/onset/duration/
velocity/articulation, tempo and dynamics curves, instrument/patch assignments,
mixing directives. Prior art to curate: Magenta NoteSequence (absolute-time
note model), MIDI 2.0 (per-note controllers), MNX (JSON notation modeling).
Feasibility grounding: expressive performance rendering literature (Performance
RNN et al.) demonstrates score → expressive performance is tractable.

The schema defines the space; the performance document is a point in it. Both
sides of that contract — interpreter and player — validate against it.
