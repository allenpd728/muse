# muse_assert — S3.5 assertions validator

Seed assertions vs. an IR work: fail loudly on violation, never silently
deviate. Design doc:
[docs/design/s3-seed-format/SPEC.md](../../docs/design/s3-seed-format/SPEC.md)
§4.

## API

```python
from muse_assert import validate_assertions, AssertionError

validate_assertions(work, assertions_dict)
```

Supported assertion kinds:

| Kind | Shape | Semantics |
|---|---|---|
| `must_contain` | `[[p1, p2, ...], ...]` | Theme pitch sequence must appear in some part |
| `register` | `{part, min, max}` | Part's pitch stays within note-name bounds (e.g. C2..C4) |
| `form` | `{sections: [...]}` | Section markers present |
| `tempo_bounds` | `{min_bpm, max_bpm}` | Tempo map within range |
| `form_curve_correlation` | `{letters: [...], window_beats?: int}` | Declared form-letter run appears as a contiguous subsequence of the work's derived form curve (via `muse_form`, window quantize A/B/C) |

Any violation raises `AssertionError(kind, detail)` with the failing part /
note / theme. Unknown assertion kinds raise
`AssertionError("unknown-assertion-kind")`.

## Dependencies

- `tools/ir` (muse_ir) for the work model.

## Tests

Test spec: [tests/open_20260823-213000_s3-assertions.md](../../tests/open_20260823-213000_s3-assertions.md).
