# Test spec: MIDI parser residual coverage (follow-up to #17)

**Source task:** #17 (MIDI parser → IR)
**Code under test:** `importer/midi.mjs` (`tests/midi.test.mjs` covers the DoD:
known fixture → notes, tempo change, meter, programs, velocity scaling, IR
validity). This spec covers what it does not.

## Behaviors to verify

- **Format 0 file** (single track, all channels interleaved) parses to one
  part — the current fixture is format 1.
- **Non-480 ppq** (e.g. 96 or 960): tick→beat conversion uses the file's own
  ppq, not a hardcoded divisor. Fixture with ppq 96, a quarter note = 96
  ticks, asserts `durationBeats === 1`.
- **Unnamed track** gets the `Track N` fallback name (IR requires non-empty).
- **Track with no program-change event** — tonejs reports `instrument.number`
  as 0 by default, indistinguishable from an explicit acoustic-grand program.
  Pin the current behavior (program 0 emitted) or teach the parser to omit it;
  either way the choice needs a test so it's deliberate.
- **Empty track** (name only, no notes) yields a part with `notes: []` and
  still validates.
- **Tempo at a non-zero tick only** (no beat-0 tempo): tempoMap reflects the
  file, synthesis decides the opening bpm — parser must not insert one.
- **Malformed input** (truncated file, garbage bytes): parser throws, error
  message does not leak a stack-trace-only failure mode when surfaced via the
  future CLI (#20). Pin that it's an `Error` with a message, not a crash.
- **Mid-piece meter change** (two time-signature events): both land in
  meterMap in beat order.

## How to run

Extend `tests/midi.test.mjs`; new fixtures alongside
`importer/fixtures/midi-sample.mid` with generators per
`make-midi-sample.mjs`. `npm test` picks the suite up automatically.

## Resolution

Residual coverage landed in `tests/midi.test.mjs` (issue #50): format 0,
non-480 ppq, unnamed-track fallback, empty track, tempo-only-at-beat-1,
mid-piece meter change, malformed input throws, and the program-default
decision pinned — `program` is now emitted only when a program-change event
exists in the file (tonejs defaults `instrument.number` to 0, which would
silently claim acoustic grand; `importer/midi.mjs` detects real program
events via a direct `midi-file` pass). New raw fixtures
(`importer/fixtures/midi-format0-ppq96.mid`, `midi-midpiece.mid`) are built
byte-by-byte in `make-raw-midi-fixtures.mjs` because tonejs only writes
format 1 at ppq 480. 19/19 standalone; npm test green.
