# W1 — Event-stream IR design doc

**Phase 0 — Analysis workbench. Status: draft (was scaffold).**

Evidence base: [../literature-review-w1.md](../literature-review-w1.md) §1,
§2, §6. The IR adopts Partitura-style structured data with full maps;
import surfaces: MusicXML (.xml/.mxl) and MIDI (.mid). Token schemes are
downstream exports (S3), not the IR.

## Purpose

Canonical in-memory event format every tool in the repo shares. Parsers:
MusicXML and MIDI. Integer ticks only — no floats. This is the seam between
source files and downstream tools (W2 loader, W3 analyzer, W4 diff, W5
visualizer), and the conceptual ancestor of S1 (on-disk freeze).

## Dependencies

- **Upstream:** none — reads corpus source files directly.
- **Downstream:** W2, W3, W4, W5; conceptually S1, and every C/L tool that
  touches the IR.

## Data model

```text
Work {
  parts: Part[]                 // one per instrument/voice
  maps: {
    tempo:  [(tick, bpm × 1000)]          // fixed-point
    meter:  [(tick, numerator, denominator)]
    key:    [(tick, fifths, mode)]
  }
  meta: { source_format, ppq, title?, warnings[] }
}

Part {
  id, name
  instrument: { name?, gm_program? }
  notes: Note[]                 // sorted by onset, deterministic
}

Note {
  pitch: int                    // MIDI number v0 (12-TET)
  onset: int_ticks
  duration: int_ticks
  velocity: 0..127              // optional; MIDI-only sources mark inferred
  articulation?: enum           // staccato, accents, tenuto, ...
  notations?: flags             // tie, slur, fermata, hairpin membership
  voice?: int                   // within-part voice index
}
```

Maps are full maps — mid-piece changes preserved (closes the old importer's
flattening bug). Dynamics are markings with tick positions; hairpins are
start/end-linked entries. Determinism: notes sorted by (onset, pitch),
against (onset, velocity, lexicographic notation) if needed to break ties
deterministically. Validation: nonnegative durations, onsets within compass
of part, maps ordered. The old schema's role vocabulary remains out of
scope; articulation/notations are preserved raw where expressed.

## Parsers

- **MusicXML (.xml/.mxl):** first-order import. Uses the existing dependency
  (partitura recommended by lit review §6; swap decision recorded in W1's
  event log if a different parser lands). Compressed .mxl handled as
  zip-member extract.
- **MIDI (.mid):** full maps from `set_tempo`/key/time-signature meta events.
  Velocity present where recorded; missing marked `inferred`. The Byrd
  corpus (MIDI-only) exercises this path; W2's loader propagates the
  `source_format=midi` flag downstream.

## Conformance (known-answer, drives W2's assertions)

| Work | Parts | Approx. notes | Map features exercised |
|---|---|---|---|
| Bach BWV227 (4 mvts) | 4 (SATB) | ~280 ea | tempo; no dynamics typical |
| Byrd Mass (6 mvts) | 3 | varies | tempo; MIDI-only path |
| Schubert D.810 | 4 | 24,772 | tempo marks; sparse dynamics |
| Beethoven 5 m.1 | 12 | 13,675 | tempo; 431 dynamics |
| Beethoven 9 | 52 | 239,459 | tempo; 11,931 dynamics |

The loader registry pins these numbers; W2 enforces them on every change.

## Open questions (draft-level)

- Articulation/notations detail: preserve umbrella where expressed; curve
  fields (chord spread, attack/release, swell, legato overlap) are delta-
  analysis-driven and remain LLM-facing (S3) rather than IR-native.
- Voice naming when source lacks it: parser marks `inferred_voice=true` per
  part; W2 surfaces it in loader summary.

## Scope

- **Inputs:** MusicXML (.xml/.mxl), MIDI (.mid).
- **Outputs:** in-memory IR object model + parser API.
- **Non-goals:** binary serialization (S1), rendering (P2/L2), pattern
  detection (W3), token export (S3).

## Acceptance criteria (when promoted to draft)

- Parses all corpus files; known-answer tests pass (note/part counts per
  [../../corpus/README.md](../../corpus/README.md)); validation hooks reject
  malformed inputs loudly; test specs open per TASK_WORKFLOW.
