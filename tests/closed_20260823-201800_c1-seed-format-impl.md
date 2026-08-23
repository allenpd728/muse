# Test spec — C1 seed format implementation (issue #148)

Written by the completing agent per TASK_WORKFLOW step 6. C1 landed with 11
CLI tests (`cd tools/muse_seed && python -m pytest`, ~1.4s; 53 total in the
package).

## Landed coverage (tools/muse_seed/test_cli.py)

- **Happy path:** the S3.6 example seed validates end-to-end (schema →
  budgets → assertions, all five stages printed); inline seed validates;
  `--work` override works; assertion failure against the real corpus work
  fails INVALID with the assertion kind named.
- **Budget checks:** tempo range exceeding every era budget rejected;
  default outside its own range rejected.
- **Schema failures:** missing file, garbage YAML, identity-guarded
  philosophy, variation region exceeding work duration — all INVALID with
  named causes.
- **show:** canonical re-serialization.

## Gaps for a `Tests:` follow-up

1. **All-seeds sweep.** When more seeds land in seeds/, a `validate-all`
   mode (or pytest walk of seeds/*.yaml) should gate the directory.
2. **dump_seed byte-fairness.** JSON round-trip byte-stability
   (dump∘load∘dump == dump) pinned for C1's machine encoding claim.
3. **muse_assert assertion vocabulary.** C1 exercises register + tempo_bounds
   via the example; must_contain and form need their own CLI-level seeds.
4. **Budget check beyond tempo.** Energy/density/variation ranges exist in
   params.py but the CLI checks tempo only; pin their checks when S3.2's
   consumer story is clearer.

## How to run

```bash
python3 tools/muse_seed/cli.py validate seeds/bwv227.1.seed.yaml
cd tools/muse_seed && python -m pytest
```
