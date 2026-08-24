# Test spec — W-B1 probe engine (task #185) — CLOSED

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

**Resolution (2026-08-24, run=20260824-1056-xtbc, #218):** 6 tests added in
`tools/muse_probes/tests/test_probes.py` (16 total in the file, 26 in the
suite) — `TestPriorRevisionWiring` pins param_diff against the committed
v1→v2 revision pair (changes == {params} exactly, from/to values pinned,
report wiring + JSON round-trip, no-prior shape);
`TestCoverageWithRealVariationPoints` uses a new fixture
`tools/muse_probes/tests/fixtures/bwv227.1.variation.seed.yaml` (region
[0,48) exercised, [145,152) unused) pinning
{variation_points: 2, exercised: 1, unused: [tempo_flex], coverage: 0.5}
with the gate still ok; `test_mockup_fn_contract` pins the MOCKUP_FN
(work → deterministic (part, pitch, onset, duration) tuples) contract the
real L1 swap must satisfy. Two spec items remain open by design: the
delta-curve era-norm line still waits on richer curve data (C3 shipped a
scalar `chord_spread_max_ioi_pstdev` bound per era, not per-era curves —
adding the era-norm line is a probe-engine change, not test coverage), and
the real-L1 swap pin activates when probes.py swaps MOCKUP_FN. Run:
`cd tools && python3 -m pytest muse_probes -q`.
