# Test spec — W-B9 workbench lineage probe (task #253)

Written 2026-08-26 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

`tools/muse_probes/probes.py` `probe_lineage()` — the eighth probe. Walks
the seed's `extends` chain via `muse_lineage.walk()` (S3.8a) and reduces
to a per-revision status: `verified` (all hops resolved) / `missing` /
`broken` / `root` (no pointer — nothing to verify) / `unknown` (no seed
path supplied). Wired into `compute_probes(..., seed_path=None)`; CLI and
`muse_explorer/generate.py` pass the path. Deliberately NOT part of the
`ok` gate. Regenerated workbench data shows root/root/verified across the
bwv227.1 revision chain.

## Coverage to write

Extend `tools/muse_probes/tests/test_probes.py` (fixtures under
`tmp_path` for the chain cases), run with
`cd tools && python -m pytest muse_probes -q`.

1. **Status reduction.** verified chain → `verified`; bare root →
   `root` (NOT `verified` — regression pin for the in-flight fix);
   unresolved pointer → `missing`; no `seed_path` → `unknown` with the
   explanatory note; hop list shape pinned.
2. **Gate orthogonality.** A seed whose lineage is `missing` but whose
   fidelity/determinism/assertions pass still yields `report.ok == True`
   (integrity is a separate signal — pin this design decision).
3. **CLI seam.** `muse-probes <seed> --out` writes the lineage block;
   exit code still driven by the three gate probes only.
4. **Explorer seam.** `generate_workbench()` output includes `lineage`
   for every seed artifact; statuses for the committed bwv227.1 chain
   pinned (`root`, `root`, `verified`).
5. **PROBe_KEYS drift guard** already pins the key set (amended in the
   landing commit) — keep it in sync with the workbench doc table.

## Known gaps (acceptable)

- The generic `probePanel` JS renders the new block without code
  changes; a dedicated DOM assertion for the lineage row belongs to the
  qa_frontend suite once its Playwright sync/async environment issue is
  fixed (pre-existing — fails identically before this change).
- Mockup-hop statuses stay `missing` until S3.8b (#254) persists
  producing mockups.

## Closed 2026-08-26 (#261, run=20260825-1033-cae1)

Extended `tools/muse_probes/tests/test_probes.py` (+7 tests, suite 29 → 36):

1. **Status reduction:** root-is-root-not-verified (the regression pin),
   verified chain (verified→root hop shape), missing pointer, unknown
   without seed_path (explanatory note pinned).
2. **Gate orthogonality:** missing lineage + green fidelity/determinism/
   assertions still yields ok=True — integrity is a separate signal.
3. **CLI seam:** muse-probes --out writes the lineage block; exit code
   unchanged by lineage status.
4. **Explorer seam:** generate_workbench artifacts all carry lineage;
   the committed bwv227.1 chain yields root + verified statuses.
5. **PROBE_KEYS** already amended by the landing commit; suite green.
