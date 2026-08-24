# Test spec — P3 conformance suite (issue #212)

**Status:** coverage landed with the implementation (43 tests, 2026-08-24,
run=20260824-1032-xjzf); this spec records what must stay green and what a
follow-up could extend.

## Behaviors to verify

- **Gate:** every registry `.mu` decodes through P1 to a canonical stream
  whose sha256 + byte count match its pin (`TestVectorGate`).
- **Store integrity:** pins.json format version, schema (source/mu/sha256/
  canonical_bytes), every registry work pinned, every pin backed by a
  `.mu` on disk, containers valid per S5 (`TestStoreIntegrity`).
- **Tamper detection:** corrupted pin hash, flipped roll byte, missing
  `.mu`, missing pin entry all FAIL — never pass, never raise
  (`TestTamperDetection`).
- **Determinism:** repeated decode of the same `.mu` is byte-identical
  (`TestDeterminism`).
- **CLI:** verify exit codes (0 green / 1 tampered), `--full`, `--vectors`,
  `dump` output shape (`TestCli`).
- **Corpus coverage:** every corpus source file has a vector; no
  machine-local paths in the store (`TestCorpusCoverage`).
- **Regeneration fidelity:** rebuilding a vector from its corpus source
  reproduces the committed pin byte-for-byte — encoder determinism
  end-to-end (`test_regeneration_reproduces_pin`).

## Edge cases covered

- Decode errors surface as FAIL results, not exceptions.
- Zip-level tampering (flipped byte inside a member) is caught by the
  hash compare even when the container still opens.
- Fast registry spans one MXL family (Bach) and one MIDI family (Byrd).

## How to invoke

```bash
cd tools && python -m pytest muse_ci/tests -q        # 43 tests, ~21s
python3 tools/muse_ci/cli.py verify --full           # the gate itself
```

## Possible follow-ups (not required to close)

- A negative-vector tier: deliberately malformed `.mu` inputs with pinned
  DecodeError classes (P1's own tests cover this at unit level today).
- Cross-decoder conformance: the store is language-agnostic by design —
  a future non-Python decoder can be gated against the same vectors.
