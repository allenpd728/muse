# System audit A1.1 — generate loop (run=20260825-1033-cae1)

Modules as one functional unit: muse_mockup (schema), muse_provider,
muse_generate. Verify-and-file; nothing fixed in the audit.

Command conventions: all run from `tools/`.

## Seams

| Seam | Command | Result | Verdict |
|---|---|---|---|
| provider fixture → generate_mockup → schema | `tests/fixtures/bwv227.1.recorded-mockup.json` + `RecordedProvider({hash(assemble_prompt(seed, work)): mockup})` then `generate_mockup(seed, work, provider)` then `validate_mockup_schema` | returns in 1 attempt, schema PASS | **works** |
| mockup dump/load round-trip | `load_mockup(dump_mockup(m))` preserves ppq=2 + notes | ppq + notes preserved | **works** |

## Modules

| Module | Doc claim | Evidence | Verdict |
|---|---|---|---|
| muse_mockup | README usage: `python3 tools/muse_mockup/cli.py <work> --out x` | ran against bwv227.1 → 279 notes, exit 0 | **works** |
| | README: schema carries `provenance.seed_hash` (L1.10) | `validate_mockup_schema` on carved dict with/without seed_hash; round-trip verified | **works** |
| | README: two file shapes + #274 resolution | both shapes constructed; dataclass dump round-trips | **works** |
| muse_provider | no README (finding) | 8 tests green | **unpinned (docs)** |
| muse_generate | no README (finding) | 10 tests green | **unpinned (docs)** |

## Findings (filed)

- muse_provider missing README → #285 (documentation)
- muse_generate missing README → #286 (documentation)
- referenced design doc `docs/design/a1-system-audit.md` absent on dev (audit design lives in the filing session's context; AGENTS.md links-checked clean otherwise)

## Unit tests (gate)

`python3 -m pytest muse_mockup muse_provider muse_generate -q` → 45 passed (muse_mockup 27, provider 8, generate 10). Full `./tools/run_tests.sh` green at end of audit.
