# muse_grow — G1 growth harness

One iteration of the seed-growth loop + comparison against the prior
delta: `grow_one(seed)` → `(delta, stand_in_flag)`; `compare_deltas(new,
prior)` → `GrowthReport` with a verdict per trait (growing / flat /
regressing). The trajectory view the workbench renders.

## Usage

```bash
python3 tools/muse_grow/cli.py <corpus-file>
python3 tools/muse_grow/cli.py <corpus-file> --prior <prior-delta.json>
python3 tools/muse_grow/cli.py <corpus-file> --seed <seed.yaml> \
    --mockup-out <path> --out <delta.json>
```

When `--mockup-out` is given, the producing mockup is persisted first
(S3.8b, #254) so the delta's `extends` names committed bytes; the
distiller stamps `extends`/`operation` (S3.7, #248). G4 (#252) logs
`expansion_time_ms` per operation tag against
`(variation_point_count, note_count)`.

## API

- `grow_one(work, seed=None, mockup_out=None, seed_path=None)` →
  `(delta, stand_in)`; the delta carries an `expansion` entry and, on
  persistence, a provenance `extends`
- `persist_mockup(mockup, out_path, seed_path=None)` → out_path
- `compare_deltas(new_delta, prior_delta, seed_id, stand_in=True)` →
  GrowthReport (per-trait verdicts)
- `MOCKUP_FN` — the deterministic stand-in; the real L1 swaps it behind
  the same pin as the probe engine (L1.11, #276)

A flat mockup means growth cannot be measured — the harness reports
`stand_in: true` (that is itself a finding).

## Dependencies

`muse_ir` (work), `muse_seed` (seed; optional), `muse_distill`
(`seed_revision` for the delta), `muse_mockup` (stand-in), `muse_lineage`
(`sha256_file` for persistence). No network calls.

## Tests

`tools/muse_grow/tests/` (G1 + G4 expansion-time + S3.8b persistence).
