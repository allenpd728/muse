# W1 — Event-stream IR design doc

**Phase 0 — Analysis workbench. Status: implemented (2026-08-23, #123 →
[tools/ir](../../tools/ir/)).**

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

| Work | Parts | Notes (written events) | Map features exercised |
|---|---|---|---|
| Bach BWV227 (4 mvts) | 4 (SATB); mvt 3 is SSATB — 5 | 279 / 377 / 307 / 190 (mvts 1/3/7/11) | tempo in mvts 1,3 only; no dynamics |
| Byrd Mass (6 mvts) | 3 | 71 / 924 / 1,440 / 327 / 130 / 384 | tempo; MIDI-only path |
| Schubert D.810 | 4 | 24,772 | tempo marks; 1,731 dynamics; 441 hairpins |
| Beethoven 5 m.1 | 12 | 13,675 | tempo; 431 dynamics; 0 hairpins |
| Beethoven 9 | 52 | 239,459 | tempo; 11,931 dynamics; 1,013 hairpins |

The loader registry pins these numbers; W1's conformance suite
(tools/ir/tests/test_conformance.py) enforces them on every change, and W2
inherits the pins.

## Open questions (draft-level)

- Articulation/notations detail: preserve umbrella where expressed; curve
  fields (chord spread, attack/release, swell, legato overlap) are delta-
  analysis-driven and remain LLM-facing (S3) rather than IR-native.
- Voice naming when source lacks it: parser marks `inferred_voice=true` per
  part; W2 surfaces it in loader summary.

## Event log (implementation, 2026-08-23)

- **Two parallel implementations raced #123** (claim collision, two sessions
  90 s apart). Retrospective review found the first landing
  (tools/muse_ir/, a7c42bb) missed the DoD: empty MusicXML maps (extract
  stub), no dynamics/hairpins, MIDI key mode hardcoded major, silent
  malformed-input drops, stale AGENTS build/test. The conformant
  implementation (tools/ir/) superseded it via review follow-up #128;
  tools/muse_ir/ removed (git history retains).
- **Unpitched percussion is a first-class event.** Beethoven 9 carries 835
  `<unpitched>` notes; they parse with `pitch=None` + the `unpitched`
  notation flag and are not rests (`is_rest` excludes them).
- **Parser swap recorded.** The issue context recommended Partitura
  (lit review §6). Measured: Partitura merges tied notes (Beethoven 5: 10,115
  events vs the registry's 13,675 written `<note>` elements) and drags a
  GPLv3 + numpy/scipy/lxml dependency tree into the parser seam. A direct
  stdlib parser (`xml.etree` + `zipfile`) landed instead; MIDI goes through
  mido's event vocabulary (MIT). Partitura remains the IR's schema reference
  and the MEI/Humdrum option; tech-stack updated.
- **Written-note fidelity is the contract.** One `<note>` element = one IR
  `Note`: ties never merged (start/stop are flags), rests are first-class
  events (`pitch=None`), chord members share onsets, grace notes have
  duration 0. S2 packs from this IR, never from a MIDI dump.
- **Rests became first-class** — the data-model sketch above predates this
  decision; lossless reconstruction requires them (a work's silence is part
  of the fixed score).
- **ppq = LCM of all `<divisions>` values in the file** — integer ticks hold
  exactly (no floats), whatever the encoder mixed in. MIDI keeps the file's
  own ticks-per-beat.
- **Map conflict policy.** Same-tick conflicting tempo/meter across parts
  (Schubert boundary artifacts) resolve first-wins with a warning in
  `meta.warnings` — the map stays a single-valued function of tick. Key
  conflicts are legitimate (transposing instruments) and every distinct
  (tick, fifths, mode) is kept.
- **Hairpin membership** is resolved at parse time: a note carries the
  `hairpin` flag iff its onset falls inside an open wedge. Hairpins
  themselves are start/end-linked entries on the part.
- **Open question settled:** `inferred_voice` is implemented — MusicXML
  parts lacking `<voice>` elements and all MIDI-derived parts mark
  `inferred_voice=true`.
- **Validation hooks:** `Work.validate()` (pitch/velocity ranges, nonnegative
  onsets/durations, deterministic ordering, ordered single-valued maps,
  unique part ids). Malformed input raises `IRParseError`; invariant
  violations raise `IRValidationError`. Nothing fails silently.

## Scope

- **Inputs:** MusicXML (.xml/.mxl), MIDI (.mid).
- **Outputs:** in-memory IR object model + parser API.
- **Non-goals:** binary serialization (S1), rendering (P2/L2), pattern
  detection (W3), token export (S3).

## Acceptance criteria (when promoted to draft)

- Parses all corpus files; known-answer tests pass (note/part counts per
  [../../corpus/README.md](../../corpus/README.md)); validation hooks reject
  malformed inputs loudly; test specs open per TASK_WORKFLOW.
