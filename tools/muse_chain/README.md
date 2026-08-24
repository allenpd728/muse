# muse_chain — E2E chain harness

Proves the pipeline stages compose: `corpus source → parse(W1) → pack(S2)
→ container(S5) → decode(P1) → verify(W4) → render(P2)`, per
[docs/design/e2e-chain-harness.md](../../docs/design/e2e-chain-harness.md).

## Usage

```bash
python3 tools/muse_chain/cli.py --all                 # full registry + report
python3 tools/muse_chain/cli.py --work bach/bwv227.1.mxl
python3 tools/muse_chain/cli.py --determinism         # two runs, compare artifacts
```

- **Stage failure isolates the owner**: stage names carry task nouns
  (`pack(S2)`), so a red stage points at one task.
- **P1/P2 are real** (#201): decode runs the P1 reference decoder
  (`tools/muse_decode`) against the written `.mu` container — the S5→P1
  seam; render runs the P2 reference renderer (`tools/muse_play`) on the
  P1-decoded Work — the P1→P2 seam — with the WAV verified (RIFF header,
  size, duration).
- **Budgets**: works over 30k notes skip the pairwise W4 diff (quadratic;
  the structural canonical compare in decode carries the losslessness
  proof there) and skip the P2 render (buffer scales with audio duration —
  B9 is ≈65 min at 44.1kHz).
- **Determinism**: artifacts are payloads (roll.bin, manifest.json), never
  zip container bytes (timestamps vary).

Report artifact: [docs/chain-report.md](../../docs/chain-report.md).

## Tests

```
cd tools/muse_chain && python -m pytest    # ~85s (B9 chain run dominates)
```
