# tools/muse_compare — L3 model comparison rig

Same score+seed, different LLM harnesses → different mockups. The rig
generates per-model seed variants (deterministic per model label), writes
mockup artifacts + a SHA-tagged ledger for blinding, and lets a listening
page hide which is which until verdict records.

## CLI

```
python -m muse_compare <work> [--models A,B] [--era classical] [--out-dir DIR]
```

## API

```python
from muse_compare import run_compare
meta = run_compare(work, "classical", ["model-x", "model-y"], out_dir)
# meta: models, artifacts per model (path+hash), ledger, deltas
```

`deltas.json` (also `meta["deltas"]`) carries the per-pair derived stats
from DoD #195: tempo default/range, tempo-flex budget, and density range
deltas per sorted model pair — params-level until a real conductor
harness plugs the mockup seam.

## Tests

```
cd tools/muse_compare && python -m pytest
```

19 tests: determinism, per-model distinct hashes, artifacts written, ledger
hashes match files, single-model ok, delta-stats shape/values/persistence,
blinding-seam pins (gap tests), CLI end-to-end.

## Note

The rig exercises the mockup harness through deterministic per-model seed
perturbation (no live API calls). Real conductor harnesses plug into this
seam; the blinding format is stable either way.
