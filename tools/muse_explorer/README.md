# muse_explorer — explorer + workbench artifact generator

Generates the committed, read-only data the QA site pages render:
`docs/explorer/{data/works.json, img/*.png}` (corpus browser + piano
rolls) and `docs/workbench/data/seeds/{index, *.probes.json,
*.directives.json}`. Read-only: the workbench is the read *surface* for
what you committed, never a write path.

## Usage

```bash
python3 tools/muse_explorer/generate.py
```

Regenerates everything the workbench/explorer render. Run after editing
a seed or committing a directive; the page's "refresh probes" note
points here.

## API

- `generate(explorer_dir=None, quick=False)` → works index (the
  explorer data)
- `generate_workbench(workbench_dir=None)` → seed index; calls
  `compute_probes` per committed seed and writes the probes JSON, the
  deduped index (content-hash dedup, #273 — byte-identical revision
  copies collapse to one entry with `aliases`), and the per-work
  `<work>.directives.json` rehearsal log
- `main()` regenerates explorer + workbench

Deterministic: same corpus → byte-identical JSON. PNGs are rerenders and
may differ at the byte level across matplotlib versions; the contract is
their existence and non-emptiness, pinned by tests.

## Dependencies

`muse_corpus` (registry), `muse_viz` (piano rolls), `muse_roll` (pack
stats), `muse_probes` (compute_probes), `muse_seed` (`load_seed`),
`muse_lineage` (`sha256_file`, `store_files`, `walk` for the directives
artifact). Reads corpus only; writes to `docs/`.

## Tests

`tools/muse_explorer/tests/` — artifact contract, page-mount safety,
the workbench dedup + no-machine-local-paths pins (#273).
