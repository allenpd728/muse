# Integration testing — scope (2026-08-23 audit)

## What exists today

~259 unit tests across 12 tool packages. All green. Each tool is tested in
isolation; seams between tools are exercised only incidentally (e.g. S2's
tests call W2's loader and W4's diff as libraries).

## What is missing

### Seam tests (pairwise contract boundaries)

| Seam | Contract | Status |
|---|---|---|
| W1 → W2 | loader's pins equal IR's parse output | covered (W2 tests) |
| W1 → W3 | analyzer reads IR via W2 | covered (W3 tests) |
| W1 → W4 | diff accepts IR directly | covered (W4 self-test) |
| W1 → W5 | visualizer reads IR | covered (W5 tests) |
| W2 → S1 | golden-vector verify uses W2 | covered (S1 tests) |
| S2 → S5 | pack payload → container member | covered (tools/muse_roll/tests, #165) |
| S5 → S2 | container read → unpack | covered (tools/muse_roll/tests, #165) |
| S1 → P1 | golden vectors → decoder input | stub contract (s1_stream DECODER pin, #168); real-P1 flip residual |
| S5 → P1 | container → decoder | covered (chain decode stage runs real muse_decode on the written .mu, #201) |
| P1 → P2 | event stream → renderer | covered (chain render stage runs real muse_play on the P1-decoded Work, #201) |
| W3 → S2 | pattern inventory informs dictionary | **not covered** (dict deferred) |

### Integration infrastructure

- **No unified test runner** — 12 pytest invocations, no single command or
  CI workflow. AGENTS.md says "CI returns with the first workflow"; it
  hasn't.
- **No shared fixture store** — each tool builds its own corpus path
  resolution. A shared `conftest.py` at `tools/` would dedupe and pin
  corpus access.
- **No golden fixture for S2** — S5 has a golden `.mu` fixture; S2 doesn't.
  A golden `(source → payload)` pair per corpus tier would catch packer
  drift.
- **No chain test** — the #162 harness is scoped but not built.

## Proposed tasks (status as of 2026-08-23 close-out)

| Task | Scope | Status |
|---|---|---|
| **T1 — Seam: S2↔S5** | pack → container member → unpack round-trip; manifest hash verification | **done** (#165, tools/muse_roll/tests) |
| **T2 — Golden fixtures for S2** | one pinned payload per corpus tier; W4 diff against re-parse | **done** (#166, tests/fixtures/) |
| **T3 — Unified test runner** | single `tools/run_tests.sh` or top-level pytest.ini that runs all suites; fast/slow split | **done** (#167, tools/run_tests.sh) |
| **T4 — Seam: S1→P1** | golden vectors feed P1's decoder when it lands | stub contract done (#168); full verification awaits P1 |
| **T5 — Chain test** | the #162 harness's test layer: full pipeline per corpus file | **done** (#169) |

T1–T3 landed 2026-08-23. T4's full verification and any further seam work
wait on P1. All are integration-layer work — no new product surface.
