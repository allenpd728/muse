# Test spec — W-B2 quality-check gate (task #186)

Written 2026-08-24 by the completing agent, per TASK_WORKFLOW §6.
Code under test: `tools/muse_probes/tests/test_quality_gate.py`.

## How to invoke

```bash
cd tools/muse_probes && python3 -m pytest   # 20 tests, <1s
./tools/run_tests.sh                        # muse_probes in fast tier
```

## Coverage landed with the task

- **Assertion regression** — previously-passing assertions must keep
  passing; the check names kind + seed on failure.
- **Budget drift** — params outside era budgets without an override note
  fail; the example seed documents its wider tempo range by design.
- **Coverage shrink** — variation points must be exercised; unused points
  name the kind.
- **Philosophy identity trip** — unlicensed identity references trip the
  guard (no license_ref).
- **Byte instability** — same seed → same mockup bytes (determinism probe).
- Each check has a positive (passes on the example seed) and a fires test
  (a constructed violation raises QualityFailure with the seed + probe).

## Behaviors still needing coverage (follow-up)

- **Cross-revision regression memory** — checks compare one revision
  against itself today; a committed prior-revision fixture pins the
  "previously passing" side when the workbench history exists.
- **Gate wiring into CI** — the runner already runs the suite; the CI gate
  (#163) should fail a push that trips a check (that wiring is #163's).
- **Era-override vocabulary** — the override note convention ("example"
  marker) is pinned by convention, not schema; S3 may want a formal
  `override_reason` field when the seed schema revs.
