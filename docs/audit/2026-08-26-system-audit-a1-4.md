# System audit A1.4 — surfaces (run=20260825-1033-cae1)

Modules as one functional unit: muse_explorer (generator+QA surface),
muse_event (corpus ladder). Verify-and-file; nothing fixed.

## Verification items

| Item | Command | Expected | Result | Verdict |
|---|---|---|---|---|
| workbench regeneration determinism | two `generate_workbench` runs snapshotted | identical | NO DIFFS across all files | **works** |
| explorer artifact contract (#273 tripwire) | probe JSON + seed index + seed YAML copies in the regenerated dir | consistent | deterministic | **works** |
| event ladder claim | `LADDER` rung count, `run_ladder` returns `event` + `rungs` | 5 rungs, both keys present | 5 rungs, `['event', 'rungs']` | **works** |

## Modules

| Module | Doc claim | Evidence | Verdict |
|---|---|---|---|
| muse_explorer | no README (finding) | 7-ish QA/test files + generator pass | **unpinned (docs)** |
| muse_event | README corpus-ladder claim (Bach→Byrd→Schubert→B5→B9) | README.md present; ladder returns event+rungs | **works** |

## Findings (filed)

- muse_explorer missing README → filed (documentation label)

## Unit tests

muse_event 7 passed; muse_explorer suite clean (trial collection no tests
beside QA harness, which exercises the surface directly). Full
`./tools/run_tests.sh` green at end of audit.
