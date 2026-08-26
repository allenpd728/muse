# Test spec — G4 expansion-time logging (task #252)

Written 2026-08-26 by the completing agent, per TASK_WORKFLOW §6.
Code under test: `tools/muse_grow/grow.py::grow_one` (expansion entry).

## Coverage landed with the task

`tools/muse_grow/tests/test_grow.py` (3 new tests, 14 total in suite):

- **Entry shape + counts** — `delta["expansion"]` carries
  `expansion_time_ms >= 0`, default operation `muse_grow@1`,
  `variation_point_count` 0 for a seedless call, `note_count` pinned to
  bwv227.1's 279 (W2 known-answer).
- **Operation tag honored** — a seed with `provenance.operation`
  (`muse_distill@2`, S3.7) keys the entry by it; variation-point count
  reflects the seed.
- **Error paths carry no phantom timing** — a failing MOCKUP_FN returns
  the error delta with no `expansion` entry.

Run: `cd tools && python3 -m pytest muse_grow/tests -q` (<1 s).

## Behaviors still needing coverage (follow-up)

- **CLI-level presence** — `muse-grow <work> --out delta.json` writes the
  expansion entry into the persisted delta (currently asserted at the
  `grow_one` level only).
- **Report-surface passthrough** — if/when the growth report JSON learns
  to carry expansion entries across revisions (the trajectory view), pin
  the passthrough.
- **Real-loop keying** — when MOCKUP_FN swaps to the real L1 generate
  loop, the operation tag should distinguish stand-in from real expansion
  times (today both would read `muse_grow@1`).

## Closed 2026-08-26 (#259, run=20260825-1033-cae1)

- **CLI-level persistence:** pinned — `test_cli_persists_expansion_entry`
  (the written delta carries operation/time/counts).
- **Report-surface passthrough:** pinned as the current contract —
  `test_expansion_entry_excluded_from_trait_compare` (compare_deltas
  ignores the entry; it is measurement, not a growth trait). Flip when
  the report learns to carry expansion entries.
- **Real-loop keying:** remains open — depends on the MOCKUP_FN swap
  (real L1), out of this suite's reach today.

Suite: `cd tools && python3 -m pytest muse_grow/tests -q` → 16 passed.
