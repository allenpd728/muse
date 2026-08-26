# muse_mockup — L1 mockup harness

Session file: tempo map, curves, velocities, balance, per-note devices
(chord spread, attack/release, swell). Generate → validate → fix loop,
validated by C1's validator. Design doc:
[docs/design/l1-mockup-harness.md](../../docs/design/l1-mockup-harness.md).

## Usage

```bash
python3 tools/muse_mockup/cli.py <work> [--out file.mockup.json]
```

Generates a complete mockup (all pitched notes, all parts) from the IR;
validates via muse_assert register bounds.

## Architecture

Iterator-safe getattr checks (sibling IR's None-pitch/sentinel field
handling); title-fidelity stays in naming (the L-series mocks are dense
DNA, not sketches, per the spike lesson).

Schema v1 (`schema/v1.json`, validated by `schema.py`) carries an optional
`provenance` object (L1.10, #250): `seed_hash` — the bare 64-hex SHA-256
of the seed the mockup realizes, i.e. the same value the next distilled
seed revision puts in `provenance.extends` (S3.7 convention; same
`is_sha256_hex` check, imported from `muse_seed`). Run-metadata fields
(`run_id`, `provider`, `model_version`, `status`) are reserved for the
typed-provider series. The earlier embedded full-`seed` property was
removed — nothing produced or consumed it.

Two file shapes exist, deliberately (#274, resolved 2026-08-26):
**dataclass dump** (`dump_mockup` — flat `notes`, `[tick, mbpm]` tempo
tuples, per-note ms fields, `ppq`) is what the mockup CLI and
`muse_grow.persist_mockup` write; it round-trips via `load_mockup` and is
the canonical shape for committed `*.mockup.json` artifacts. **Schema
v1.json** (parts mapping, `{tick, bpm}`, sec fields) is the in-flight
session-file contract for the L-series generate loop — the shape the
generation pass validates against. `provenance.seed_hash` is the only
provenance field the dump shape needs today; the lineage walker
(`muse_lineage`) reads provenance structurally and is shape-agnostic. The
dump shape dropping `attack/release` is the stand-in's flat data, not a
lossy mapping — when the real L1 emits those fields, reconsider then
whether the dump should grow to schema-shape.

## Tests

Test spec: [tests/open_20260823-235000_l1-mockup.md](../../tests/open_20260823-235000_l1-mockup.md).
