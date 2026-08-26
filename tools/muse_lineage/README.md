# muse_lineage — S3.8a chain-walk/verify helper

Walks an artifact's lineage backward through the store: each hop follows
`provenance.extends` (seeds, S3.7) or `provenance.seed_hash` (mockups,
L1.10) to the parent artifact whose **committed file bytes** hash to that
value. Design: [docs/design/proposal-lineage-chain.md](../../docs/design/proposal-lineage-chain.md)
§1 (bare 64-hex SHA-256, no prefix, no canonicalization).

## Usage

```bash
python3 tools/muse_lineage/cli.py walk seeds/bwv227.1.v2.seed.yaml [--store DIR ...]
python3 tools/muse_lineage/cli.py walk <seed> --json
python3 tools/muse_lineage/cli.py verify <child> <parent>
```

`walk` prints one line per hop and exits 0 when every hop is
`verified`/`root`, 1 on `missing`/`mismatch`/`cycle`, 2 on usage/parse
errors. Default store: repo `seeds/`; candidate parents are
`*.seed.yaml` and `*.mockup.json` under each store dir (recursive).

## Per-hop states

| Status | Meaning |
|---|---|
| `verified` | a store file's bytes hash to the pointer |
| `missing` | no store file matches (deleted / never committed / corrupted in place — indistinguishable by hash alone) |
| `mismatch` | explicit pair check only: the named parent's bytes do not hash to the child's pointer |
| `root` | no pointer — the chain's origin |
| `cycle` | a visited file re-entered (unreachable with content hashes short of a collision; kept as cheap insurance) |

## Semantics

- The pointer names **content, not a path**: if two committed files are
  byte-identical, either may resolve as the parent (the store scan is
  sorted, so resolution is deterministic).
- Mockup hops report `missing` until S3.8b (#254) lands and the growth
  loop starts committing producing mockups — expected, not an error.
- `operation` is informational and never verified.

## API

```python
from muse_lineage.lineage import walk, verify_pair, find_by_hash, sha256_file

hops = walk("seeds/bwv227.1.v2.seed.yaml", ["seeds"])   # list[Hop]
verify_pair("child.seed.yaml", "parent.seed.yaml")      # "verified" | "mismatch"
```

## Dependencies

`pyyaml` (seed parsing), stdlib otherwise. Does not import `muse_seed` —
the walker reads provenance structurally so it can walk artifacts whose
schemas evolve.

## Tests

Spec: [tests/open_20260826-002500_s3-8a-chain-walk.md](../../tests/open_20260826-002500_s3-8a-chain-walk.md).
