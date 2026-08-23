# muse_probes — W-B1 seed-iteration probe engine

Per seed revision, compute the seven probes from
[docs/design/seed-workbench.md](../../docs/design/seed-workbench.md) and emit
a deterministic JSON artifact the workbench page renders. Read-only over the
S3/C1/C3/L1 toolchain; nothing new is generated.

## Probes

| Probe | Question |
|---|---|
| param_diff | what changed vs the prior seed revision |
| budget_fit | do seed ranges sit inside the era's measured budgets (C3) |
| assertions | do the seed's assertions hold against the work (S3.5) |
| coverage | which sanctioned variation points the mockup exercises (S3.4) |
| delta_curves | mockup IOI shape vs source (W3 vocabulary) |
| determinism | same generation path twice → identical artifact |
| fidelity_guard | mockup never contradicts the score (tolerance 0) |

## Usage

```bash
python3 tools/muse_probes/cli.py seeds/bwv227.1.seed.yaml
python3 tools/muse_probes/cli.py <seed> --prior <prior-seed.yaml>
python3 tools/muse_probes/cli.py <seed> --out probes.json
```

Exit 0 when the gate probes pass (fidelity + determinism + assertions);
1 otherwise. The mockup path is the deterministic L1 stand-in
(`MOCKUP_FN` in probes.py); the real L1 generate loop swaps it when it
lands — same contract as the P1 DECODER pin.

## Tests

```bash
cd tools/muse_probes && python3 -m pytest
```
