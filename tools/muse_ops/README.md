# muse_ops — S4 language validator

Grammar-only validator for `.mu` programs, per
[FORMAT_SPEC §5.1](../../FORMAT_SPEC.md) and
[docs/design/s4-language-spec.md](../../docs/design/s4-language-spec.md).

## Usage

```python
from muse_ops import validate_program, OpsError

validate_program([
    {"op": "ptn_exact", "region": [0, 768], "part": "P1"},
    {"op": "ptn_transposed", "region": [768, 1536], "interval": "+2"},
    {"op": "ptn_ostinato", "region": [0, 1536]},
], duration_ticks=1536)   # optional work-bounds check
```

Shipped operators (W3 corpus evidence): `ptn_exact`, `ptn_transposed`,
`ptn_ostinato`. Deferred (no evidence): `ptn_invert`, `ptn_retro`,
`ptn_imitative`. Grammar only — semantics are P1's decoder.

## Tests

```
cd tools/muse_ops && python -m pytest
```
