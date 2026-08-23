# muse_chain — E2E chain harness

Proves the pipeline stages compose: `corpus source → parse(W1) → pack(S2)
→ container(S5) → decode(P1-stub) → verify(W4) → render(P2)`, per
[docs/design/e2e-chain-harness.md](../../docs/design/e2e-chain-harness.md).

## Usage

```bash
python3 tools/muse_chain/cli.py --all                 # full registry + report
python3 tools/muse_chain/cli.py --work bach/bwv227.1.mxl
python3 tools/muse_chain/cli.py --determinism         # two runs, compare artifacts
```

- **Stage failure isolates the owner**: stage names carry task nouns
  (`pack(S2)`), so a red stage points at one task.
- **P1/P2 are stubs** (SKIP, not FAIL): decode runs S2's decoder as a
  stand-in until the sandboxed P1 lands; render waits for P2.
- **W4 budget**: works over 30k notes skip the pairwise diff (quadratic);
  the structural canonical compare in decode carries the losslessness
  proof there.
- **Determinism**: artifacts are payloads (roll.bin, manifest.json), never
  zip container bytes (timestamps vary).

Report artifact: [docs/chain-report.md](../../docs/chain-report.md).

## Tests

```
cd tools/muse_chain && python -m pytest    # ~85s (B9 chain run dominates)
```
