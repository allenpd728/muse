# Bug — muse_author CLI drops era_budget at the Seed/YAML seam

**Found:** 2026-08-24, run=20260824-1032-xjzf, while working Tests: C3
(#215, spec tests/open_20260823-222856_c3-budget-calibration.md gap 2).

## Symptom

`muse_author._propose` returns `era_budget` on the seed dict (author.py),
but `tools/muse_author/cli.py` rebuilds the proposal as a `Seed(...)`
dataclass — which has no `era_budget` field — before `dump_seed`. The
written proposal YAML therefore never carries the budget, and
`muse_seed_cli validate` (C1) cannot assert its presence on authored
proposals, which the C3 test spec calls for ("muse_seed_cli validation
should assert its presence on authored proposals").

## Repro

```bash
python3 tools/muse_author/cli.py corpus/byrd/1-Kyrie.mid --era baroque --out /tmp/p.yaml
grep era_budget /tmp/p.yaml   # no match — dropped
```

## Root cause

`Seed` (tools/muse_seed/seed.py) models the S3 seed schema; `era_budget`
is an authoring-time annotation outside that schema. Whether it belongs
in the seed format (schema addition) or is validation-side metadata is a
format decision — per the format-first ground rule it needs a FORMAT_SPEC
/ S3 call, not a hard-coded tool change.

## Fix (one of)

- Add `era_budget` (optional) to the S3 seed schema + `Seed`, so authored
  proposals carry it end-to-end and C1 asserts its presence; or
- Decide `era_budget` is proposer-internal, amend the C3 test spec gap 2
  wording, and close this as intended behavior.

## Impact

Low today: tempo bounds in authored proposals are *derived* from the
budget (default = budget midpoint, tested), so the budget's influence is
present even though the annotation is dropped. The gap is auditability —
a reviewer of a proposal YAML cannot see which budget sanctioned it.

---

**Closed:** 2026-08-24, run=20260824-2254-2185, issue #236.
**Resolution:** schema path — `era_budget` added to the S3 seed schema as
an optional top-level field (decision recorded in
`docs/design/s3-seed-format/SPEC.md` decisions log). `Seed` carries it
end-to-end (`load_seed`/`dump_seed`/`validate_seed`; mapping-when-present),
`muse_author` CLI passes it through the rebuild, and C1
(`muse_seed_cli validate`) fails authored proposals
(`provenance.author: muse_author`) that lack it. Hand-authored seeds
without the field still validate. Tests:
`tools/muse_seed/test_era_budget_seam.py` (8 tests) — round-trip,
absent-stays-absent, non-mapping rejection, C1 presence assertion,
author-CLI end-to-end.
