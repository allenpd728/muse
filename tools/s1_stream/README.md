# tools/s1_stream — S1 golden vectors

Per [FORMAT_SPEC.md §4.4](../../FORMAT_SPEC.md): (source → canonical JSON
dump) pairs pinned by the W4 diff tool. JSON is the human-readable
interchange encoding only; the binary layout belongs to S2.

## Commands

```
cd tools/s1_stream
PYTHONPATH=../ir:. python -m muse_stream.golden generate <source> -o <vector.json>
PYTHONPATH=../ir:. python -m muse_stream.golden verify <source> <vector.json>
```

`verify` exits 0 on byte-exact match, 1 otherwise (CI gate).

## Canonical form

`json.dumps(sort_keys=True, separators=(",", ":")) + "\n"`, integers only.
Structure pinned by FORMAT_SPEC §4.1–4.4: meta / full maps / parts with
dynamics, hairpins, and every note (rests, ties, grace, chord, unpitched
all preserved).

## Committed golden vectors

`golden/`: bach_bwv227.1, byrd_1-kyrie, schubert_d810, beethoven_sym5_mov1.
Regenerate after any IR change and re-pin; the W4 diff catches drift.

## Tests

```
cd tools/s1_stream && python -m pytest
```

6 tests: determinism, structure, round-trip verify, tamper detection,
dynamics/hairpin serialization, unpitched preservation.
