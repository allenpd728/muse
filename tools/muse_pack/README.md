# muse_pack — S2 roll encoding

Packer/decoder for the score roll: columnar channels per part → delta-encoded
onsets → zlib (entropy). Round-trips the corpus losslessly against W4's diff
ground truth (recall == precision == 1.0 on every corpus file).

## Usage

```bash
# W4-gate one file
python3 tools/muse_pack/cli.py roundtrip corpus/schubert/death-and-the-maiden.mxl
# Full corpus sweep
python3 tools/muse_pack/cli.py --self-test
```

Programmatic:

```python
from muse_pack.pack import pack, unpack
from muse_pack.rebuild import unpack_to_canonical
payload = pack(work)            # Work → bytes (MAGIC + zlib'd JSON)
chan = unpack(payload)          # bytes → channel dict
canon = unpack_to_canonical(chan)  # channel dict → canonical S1 shape
```

## Channel layout (v0)

Per part, note-indexed (position i = IR-sorted note i):

- `pitch` — MIDI number, -1 for rests/unpitched
- `onset_delta` — onset[i] − (onset[i−1] + duration[i−1]); absolute recovery
- `duration` — source ticks; 0 for grace notes
- `voice` — -1 for None, else ≥1
- `velocity` — -1 for None, else 0..127
- `notations` — bitmask over the flag vocabulary (tie/slur/fermata/hairpin/
  grace/chord/unpitched)
- `articulations` — bitmask over the articulation vocabulary

Maps, meta, dynamics, hairpins ride verbatim in the payload. The dictionary
pass is explicitly not v0: DEFLATE owns entropy; pattern-factoring lives at
the W3 layer. The W4 diff (recall == precision == 1.0) is the gate — see
[tests/](tests/).

## Tests

```bash
cd tools/muse_pack && python3 -m pytest
```
