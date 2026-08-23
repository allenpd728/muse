# muse_seed_cli — C1 seed validator micro-pipeline

The tester/validator session's first workbench: read/write seeds, validate
budgets against era-calibrated ranges, check assertions against corpus
works. Design doc:
[docs/design/c1-seed-format-impl.md](../../docs/design/c1-seed-format-impl.md).

## Usage

```bash
python3 tools/muse_seed_cli/cli.py read <seed.yaml>
python3 tools/muse_seed_cli/cli.py validate <seed.yaml> <work>
python3 tools/muse_seed_cli/cli.py budget-check <era> [--nominal-bpm N]
```

`validate` runs: schema check → assertion check → tempo-bounds sanity →
era-budget check (when provenance.era is set). Exit 0 on pass, 1 on fail.

## Architecture

Composes the S3 sub-task modules:

| Module | Role | From |
|---|---|---|
| `tools/muse_seed` | schema + YAML/JSON I/O | S3.1 |
| `tools/muse_seed/params.py` | era-calibrated budgets | S3.2 |
| `tools/muse_assert` | assertion validation | S3.5 |
| `seeds/bwv227.1.seed.yaml` | example seed | S3.6 |

## Tests

Test spec:
[tests/open_20260823-220000_c1-seed-validator.md](../../tests/open_20260823-220000_c1-seed-validator.md).

## What comes next

C2 (AI-assisted authoring) consumes this validator in the generate →
validate → fix loop: an LLM proposes a seed, this CLI validates it,
failures feed back as revision prompt.
