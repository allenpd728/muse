# Test spec — R3 conductor-training study scripts (task #284) — CLOSED

**Resolution (R3 #284, 2026-08-26, run=20260825-2247-qogi):** landed in
`tools/muse_study/tests/test_study.py` (8 tests): scripts have steps +
valid-grammar verbs, per-step survival reports, rebalance survival moves
part_gains with the correct *sign* (regression pin: a "down" directive
must lower gain — the direction-word-order bug made "bring … down" parse
as up), phrase counts variation_points, hold adds tempo_bounds, flat
when nothing changes. Suite: `cd tools && python -m pytest muse_study -q`
→ 8 passed. CLI: `tools/muse_study/cli.py list|run`.

## What landed

`tools/muse_study/` (study.py, cli.py, README, tests). Four precomposed
scripts (quiet-the-bass, phrase-the-pickup, tempo-architecture,
rubato-calibration) keyed to well-known interpretive issues. Survival
feedback maps each verb to its seed knob and reports moved/flat/drifted
per step, at the **seed-param level** — the render level is
stand-in-blocked until the real L1 lands (#276), and the doc says so.

## Bug found + fixed in flight (cross-module, in muse_rehearse)

`_parse_direction` matched direction words in dict order, so
"rebalance: bring P4 down" parsed as +1 (matched "bring" before "down").
The operative direction word is the LAST one; fixed and regression-pinned
in both muse_rehearse and muse_study test suites.
