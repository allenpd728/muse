# muse_ir — W1 event-stream IR

Canonical in-memory event format for all Muse tools. Integer ticks only.

## Usage

```python
import sys; sys.path.insert(0, 'tools')
from muse_ir import load

work = load('corpus/bach/bwv227.1.mxl')   # or .xml, .mid
print(work.parts, work.note_count, work.maps)
```

## Conformance

```bash
python3 tools/muse_ir/conformance.py
```

All 13 corpus cases must pass (part counts + note/event counts per
corpus/README.md, measured). Beethoven 9: 52 parts, 239,459 events.

## Model

- `Work`: parts, maps (tempo/meter/key — full maps), source_format, ppq
- `Part`: id, name, gm_program, notes (deterministically sorted)
- `Note`: pitch (-2=unpitched, -1=rest, 0–127=MIDI), onset, duration (ticks),
  velocity, articulation, notations (tie/grace/unpitched flags), voice

Parsers: MusicXML via partitura, MIDI via mido. Dependencies:
`pip install partitura mido`.
