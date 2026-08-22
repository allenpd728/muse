# Test spec: manual paste mode residual coverage (follow-up to #108)

**Source task:** #108 (`--manual` interpreter mode)
**Code under test:** `interpreter/expand.mjs` manualCall + CLI flag handling
(`tests/interpreter-manual.test.mjs` covers DoD: prompt printed, stdin read,
provenance stamped "manual", flag parsing, junk-paste error). This spec covers
what remains.

## Behaviors to verify

- **`--manual` via env var**: `MUSE_MANUAL=1` takes the same path as the flag.
- **tools/play.mjs manual path**: `node tools/play.mjs <doc> --manual` wires
  manual mode through the play CLI (currently manual mode lives only in
  expand.mjs — pin or extend).
- **Retry feedback visible to the human**: on a schema failure, the second
  prompt carries the validation error text (interactive loop — assert the
  stderr of the second attempt includes the error, using a two-paste stdin).
- **Provenance claim via flag**: if a `--manual-model "gpt-4o"` style override
  lands, the stamp uses it; otherwise pin that "manual" is the only stamp.

## How to run

`npm test`; the interactive two-paste retry is scripted via spawnSync input.
