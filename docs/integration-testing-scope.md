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
| S2 → S5 | pack payload → container member | **not covered** |
| S5 → S2 | container read → unpack | **not covered** |
| S1 → P1 | golden vectors → decoder input | **not covered** (P1 todo) |
| S5 → P1 | container → decoder | **not covered** (P1 todo) |
| P1 → P2 | event stream → renderer | **not covered** (P1/P2 todo) |
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

## Proposed tasks (not started)

| Task | Scope | Blocked by |
|---|---|---|
| **T1 — Seam: S2↔S5** | pack → container member → unpack round-trip; manifest hash verification | S2, S5 (done) |
| **T2 — Golden fixtures for S2** | one pinned payload per corpus tier; W4 diff against re-parse | S2 (done) |
| **T3 — Unified test runner** | single `tools/run_tests.sh` or top-level pytest.ini that runs all suites; fast/slow split | none |
| **T4 — Seam: S1→P1** | golden vectors feed P1's decoder when it lands | P1 (todo) |
| **T5 — Chain test** | the #162 harness's test layer: full pipeline per corpus file | #162, P1 |

T1–T3 are unblocked and scoped to fit in one agent run each. T4–T5 wait on
P1. All are integration-layer work — no new product surface.
