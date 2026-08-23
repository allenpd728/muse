# Test spec — W-B1 probe engine (task #185)

Written 2026-08-24 by the completing agent, per TASK_WORKFLOW §6.
Code under test: `tools/muse_probes/`.

## How to invoke

```bash
cd tools/muse_probes && python3 -m pytest   # 10 tests, <1s
python3 tools/muse_probes/cli.py seeds/bwv227.1.seed.yaml
```

## Coverage landed with the task

- **All seven probes present** in every report (param_diff, budget_fit,
  assertions, coverage, delta_curves, determinism, fidelity_guard).
- **Determinism:** identical seed+work → identical probe JSON.
- **Fidelity guard:** clean mockup passes; missing note fails with count.
- **Param diff:** mutation between revisions detected.
- **Budget fit:** range/budget/inside/position fields pinned.
- **Assertions:** per-kind pass/fail with register+tempo_bounds coverage.
- **Gate:** report.ok flips on a failing gate probe (real failing assertion).
- **CLI:** stdout JSON, --out write, exit 0/1 by gate.

## Behaviors still needing coverage (follow-up)

- **Prior-revision wiring** — param_diff tested with an in-memory mutation;
  a committed two-revision fixture (seed v1 → v2 with a known diff) pins the
  comparison shape the workbench history rows consume.
- **Coverage with real variation points** — the example seed has
  variation_points: []; a seed with actual regions pins exercised/unused.
- **Delta-curve era-norm comparison** — today source-vs-mockup only; the
  era-norm line waits on C3's richer curve data.
- **Real-L1 swap** — MOCKUP_FN is the deterministic stand-in; the day the
  L1 generate loop lands, the pin runs against it unchanged.
