# muse_decode — P1 reference decoder

`.mu` container (manifest.json + roll.bin) → event stream. Deterministic,
sandboxed, resource-bounded. Design doc:
[docs/design/p1-reference-decoder.md](../../docs/design/p1-reference-decoder.md).

## Usage

```bash
python3 tools/muse_decode/cli.py file.mu
```

Decodes the S2 pack into the W1 IR Work; prints parts + note count; exit 0
on success. Invalid container → exit 1 with DecodeError.

## Architecture

S5 container read (zip, required members) → S2 roll decode via muse_roll →
Work. No intelligence; the decoder is dumb (locked).

## Tests

Test spec: [tests/open_20260824-020000_p1-decoder.md](../../tests/open_20260824-020000_p1-decoder.md).
