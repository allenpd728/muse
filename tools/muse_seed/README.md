# muse_seed — S3.1 container & encoding

Seed bytes reader/writer + validator per
[docs/design/s3-seed-format/SPEC.md](../../docs/design/s3-seed-format/SPEC.md).

## Usage

```python
from muse_seed import Seed, load_seed, dump_seed, validate_seed

seed = load_seed(yaml_text, fmt="yaml")
dump_seed(seed, fmt="json")   # byte-fair machine encoding
validate_seed(seed)           # raises SeedError on schema violation
```

Top-level keys: format_version, work_id, title, params, philosophy,
variation_points, assertions, provenance. Required: format_version,
work_id, params, assertions.
