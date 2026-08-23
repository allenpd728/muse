# W1 — Event-stream IR (design doc, scaffold)

**Phase 0 — Analysis workbench. Status: scaffold.**

## Purpose

Canonical in-memory event format that every tool in the repo shares: notes
(pitch/onset/duration/velocity), parts, tempo/meter/key maps, dynamics,
articulations. Parsers: MusicXML and MIDI. Integer ticks only — no floats.
This is the seam between source files and every downstream tool.

## Dependencies

- **Upstream:** none — reads corpus source files directly.
- **Downstream:** W2, W3, W4, W5; conceptually S1 (which freezes it on disk),
  and every C/L tool that touches the IR.

## Scope (pin in draft)

- **Inputs:** MusicXML (`.xml`/`.mxl`), MIDI (`.mid`).
- **Outputs:** in-memory IR object model + parser API.
- **Non-goals:** binary serialization (S1), rendering (P2/L2), pattern
  detection (W3).

## Open questions

- Articulation/voice representation detail needed by delta-analysis devices
  (chord spread, attack/release/swell, legato overlap).
- Fermata/repeat-topology handling — full maps, per FORMAT_SPEC §4.

## Acceptance criteria (when promoted to draft)

- Parses all corpus files; known-answer tests pass (note/part counts per
  [../../corpus/README.md](../../corpus/README.md)).
