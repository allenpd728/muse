# tools/muse_distill — L4 distiller

Mockup → extracted interpretation → human-reviewable seed revision. The
learning loop makes later mockups cheaper and better.

## CLI

```
python -m muse_distill <mockup.json> [--out delta.yaml] [--format yaml|json]
```

## API

```python
from muse_distill import extract_interpretation, seed_revision, dump_delta
i = extract_interpretation(mockup)
d = seed_revision(mockup)
yaml_out = dump_delta(d, fmt="yaml")
```

## Extract

- tempo curve shape (flat | arch | wavering)
- tempo bpm range, velocity mean/pstdev, rubato mean/pstdev
- per-part note counts (gains)

## Tests

```
cd tools/muse_distill && python -m pytest
```

5 tests: stats, flat/arch shape classification, revision shape, dual-format dump.
