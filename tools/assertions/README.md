# tools/assertions — C4 assertion vocabulary

Authored per-work assertion sets, derived from the **measured** bounds on
each corpus source (register limits from the work's pitch extremes, tempo
bounds from its tempo map). Reads through S3.5's `muse_assert` validator.

The authoring mechanism: read the work, take its measured bounds, pin
them; violation fails loudly on out-of-range performance.

## Authored works

- **BWV227.1** — register G2–G5, tempo 60–180
- **Schubert D.810** — register C2–D7, tempo 40–320

## API

```python
from vocabulary import AUTHORED, get
get("BWV227.1")  # dict, or {} for unknown
from muse_assert import validate_assertions
validate_assertions(work, get("BWV227.1"))  # raises loud on violation
```

## Tests

`cd tools/assertions && python -m pytest` (6 tests, ~1 s).
