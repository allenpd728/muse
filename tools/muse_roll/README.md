# muse_roll — S2 roll encoding

Lossless packing of the W1 IR into `roll.bin`, per
[FORMAT_SPEC §4.6](../../FORMAT_SPEC.md) and
[docs/design/s2-score-encoding.md](../../docs/design/s2-score-encoding.md).

## Format (R1)

`MUR1` magic + varint(compressed length) + zlib payload. Inside the
payload: string table, JSON meta, delta-encoded maps, then parts with
columnar note streams — onset deltas (zigzag varints), presence-bitmap
optional fields, dictionary-coded articulations/notations/dynamics/hairpin
kinds. Stdlib only (zlib; no external entropy coder).

## Usage

```bash
python3 tools/muse_roll/cli.py pack <work> -o <roll.bin>
python3 tools/muse_roll/cli.py verify <work> <roll.bin>   # W4 ground truth
python3 tools/muse_roll/cli.py unpack <roll.bin>
```

`verify` runs the round-trip through W4's diff tool: exit 0 only when
recall = precision = 1.0 (LOSSLESS).

Measured on the corpus (2026-08-23): Bach ~10–12% of .mxl source, Byrd
MIDI ~14–22%, Schubert 9.6%, Beethoven 5 0.26% (4.75 MB → 12.5 KB),
Beethoven 9 0.24% (68.8 MB → 168 KB, encode 0.8s). Every file:
lossless (W4 verify; B9 structurally).

## Tests

```
cd tools/muse_roll && python -m pytest
```
