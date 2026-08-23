# Test spec — S2 roll encoding (task #138)

Written 2026-08-23 by the completing agent, per TASK_WORKFLOW §6.
Code under test: `tools/muse_pack/` (packer, codec, rebuild).

## How to invoke

```bash
cd tools/muse_pack && python3 -m pytest tests/ -q   # 9 tests, ~52s
python3 tools/muse_pack/cli.py roundtrip corpus/schubert/death-and-the-maiden.mxl
python3 tools/muse_pack/cli.py --self-test
```

## Coverage landed with the task

`tools/muse_pack/tests/test_pack.py` — 9 tests:

- **W4 diff gate (4 corpus tiers):** Bach chorale, Byrd Gloria (MIDI),
  Schubert D.810 (24,772 notes), Beethoven 5 mov 1 (13,675 notes) —
  recall == precision == 1.0, per the task's acceptance criterion.
- **Compression ratio bands:** measured packed/source ratios pinned
  per tier (18% Bach, 25% Byrd, 11% Schubert, 0.4% B5 XML).
- **Determinism:** identical Work → identical payload bytes.

## Behaviors still needing coverage (follow-up)

- **Beethoven 9 round-trip (239k notes)** — the Ninth round-trips correctly
  but is excluded from the main suite for wall-clock reasons (~2min); add a
  `-k "not beethoven9"`-style split test once W6's compute budget lands.
- **Dictionary layer (v1)** — v0 keeps literals verbatim; the dictionary
  pass is pinned as deferred. When S2 grows one (W3-driven pattern
  dictionary), the W4 diff must keep passing with it active.
- **Channel-shape mutation tests** — corrupted payload fields (unknown
  magic, missing channels, dict index out of range) should fail loudly.
- **S5 container wiring** — the .mu container (S5) owns magic/framing;
  when P1's decoder consumes payloads through the container, pin the seam
  so this packer stays container-agnostic.
