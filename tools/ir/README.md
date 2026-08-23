# tools/ir — W1 event-stream IR

The canonical in-memory event format every Muse tool shares, plus parsers for
MusicXML (`.xml`/`.mxl`) and MIDI (`.mid`). Design:
[docs/design/w1-event-ir.md](../../docs/design/w1-event-ir.md).
Integer ticks only — no floats.

## API

```python
from muse_ir import load  # dispatches on extension

work = load("corpus/bach/bwv227.1.mxl")
work.parts          # Part[] — one per instrument/voice (MIDI: per note-bearing track)
work.maps.tempo     # [(tick, bpm * 1000)] — full map, mid-piece changes preserved
work.maps.meter     # [(tick, numerator, denominator)]
work.maps.key       # [(tick, fifths, mode)] — multi-valued per tick (transposing parts)
work.meta           # source_format, ppq, title, warnings[]
work.note_count     # every written note element, incl. rests
work.duration_ticks()

part = work.parts[0]
part.notes          # Note[], sorted deterministically: (onset, pitch, velocity,
                    # lexicographic notations, voice, source_id)
part.dynamics       # DynamicMarking[(tick, text)] — e.g. "p", "ff"
part.hairpins       # Hairpin(kind, start_tick, end_tick) — start/end linked
part.instrument     # name?, gm_program? (MIDI sources)

note = part.notes[0]
note.pitch          # MIDI number, or None for rests (rests are first-class events)
note.onset          # int ticks
note.duration       # int ticks; 0 for grace notes
note.velocity       # 0..127 or None; velocity_inferred flag when synthesized
note.articulations  # tuple of MusicXML articulation tags, as expressed
note.notations      # frozenset: tie_start/stop, slur_start/stop, fermata,
                    # hairpin (membership), grace, chord, unpitched
```

Unpitched percussion (`<unpitched>`) parses with `pitch=None` plus the
`unpitched` flag — an event, not a rest (Beethoven 9 carries 835 of them).

## Fidelity contract

One `<note>` element = one `Note`. Tied notes stay separate (tie start/stop are
flags, never merged); rests, chord members, and grace notes are events. This is
what the conformance registry ([corpus/README.md](../../corpus/README.md))
pins, and what S2's lossless packing needs — S2 packs from the IR, never from
a MIDI dump.

Maps are **full maps**: mid-piece tempo/meter/key changes are preserved.
Same-tick conflicting tempo/meter values across parts resolve first-wins with
a warning in `meta.warnings` (sloppy encodings); key conflicts are legitimate
(transposing instruments) and every distinct value is kept.

Malformed input fails loudly with `IRParseError` (never partial results);
model invariants are enforced by `Work.validate()` → `IRValidationError`.

## Dependencies

- MusicXML path: Python stdlib only (`xml.etree`, `zipfile`).
- MIDI path: [`mido`](https://mido.readthedocs.io) (event vocabulary only;
  pairing/maps/parts are ours).

The issue context recommended Partitura; a direct parser landed instead
because Partitura merges tied notes (B5: 10,115 events vs the registry's
13,675). Swap recorded in the W1 commit and the design doc's event log.

## Tests

```
pip install -r tools/ir/requirements.txt
cd tools/ir && python -m pytest
```

58 tests: corpus known-answer conformance (all five works), MusicXML/MIDI unit
tests, model invariant tests. The full suite runs in ~11 s, Beethoven 9
included.
