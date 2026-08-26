# Bug — workbench seed index duplicates revisions (same block rendered twice)

**Found:** 2026-08-26, run=20260824-1032-xjzf, founder report on the QA
site: "Audio — seed revisions shows up twice on their page."
**Issue:** filed from this entry (see issue number in the done/closed
rename).

## Symptom

`docs/workbench/detail.html` renders the entire bwv227.1 block — seed
panel, probes, growth, audio — twice (three times once a v3 lands). The
seed index (`docs/workbench/data/seeds/index.json`) lists three entries
for one work, of which `bwv227.1.seed.yaml` and `bwv227.1.v1.seed.yaml`
are byte-identical files.

## Root cause

`tools/muse_explorer/generate.py::generate_workbench` indexes *every*
`.seed.yaml` in `seeds/` — no dedup by content and no revision awareness.
Two revision files with identical content (a copy-checkpoint convention
that predates the lineage pointer, per S3.7) produce two index entries;
the page groups nothing, so each entry is its own block.

## Secondary findings (same regeneration, commit 32f8e9f)

1. **Lineage artifacts are stale**: the committed v1/v2 probe artifacts
   show `lineage: root` with empty pointers, but `bwv227.1.v2.seed.yaml`
   carries a real `extends` hash and a fresh `probe_lineage` run returns
   `verified` (v2 → root chain). The committed artifacts predate or
   mis-wired the seed_path.
2. **Machine-local absolute paths in committed artifacts**: hops carry
   `/workspace/project/muse/seeds/...` — the leak class s1_stream's
   `test_no_machine_local_paths_in_vectors` pins against. Lineage hops
   should store repo-relative paths.

## Fix

- Dedup in `generate_workbench`: group seeds by content hash (or skip a
  file whose bytes duplicate an already-indexed revision); keep one index
  entry per distinct revision.
- Regenerate workbench data so v2's lineage shows `verified`; make hops
  repo-relative before writing.
- Regression pin: workbench index never lists two entries whose seed
  files are byte-identical.

## Impact

Cosmetic-but-loud on the page (duplicate panels), and the lineage probe's
committed evidence contradicts the seeds it describes — the W-B9 feature
reads broken on its own demo data.
