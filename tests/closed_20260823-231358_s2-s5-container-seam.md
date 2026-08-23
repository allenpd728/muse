# Test spec — S2↔S5 container seam (issue #165) — CLOSED

The task was itself the test work (a seam-coverage task from the
integration-testing scope audit, T1), so this spec is filed closed: it
records the coverage that landed rather than requesting it. No recursive
`Tests:` follow-up is filed for a test-only task.

**Resolution (2026-08-23, run=20260823-2312-h8pk):** 8 tests in
`tools/muse_roll/tests/test_container_seam.py`, green in the unified
runner's fast tier inside the `muse_roll` suite (51 passed).

## Landed coverage (tools/muse_roll/tests/test_container_seam.py)

- **Round-trip, three corpus tiers** (Bach `bwv227.1.mxl`, Byrd
  `1-Kyrie.mid`, Schubert `death-and-the-maiden.mxl`): load → S2 `encode`
  → S5 `write_mu` → `read_mu` → S2 `decode` → W4 `diff` —
  recall = precision = 1.0 on every tier; payload byte-exact through the
  zip container.
- **Manifest hash pins the payload**: `hashes["roll.bin"]` equals the
  packed payload's sha256 at build time and after read-back; cross-pinned
  against T2's golden roll vector (`tests/fixtures/bwv227.1.roll.bin`) so
  packer drift fails the seam suite too.
- **Corruption is loud, never silent partial data**:
  - tampered `roll.bin` with the original manifest → `read_mu` raises
    `ManifestError` (hash mismatch);
  - tampered payload hidden by re-hashing (corrupt MAGIC, honest
    manifest) → container read passes, S2 `decode` raises `RollError`;
  - `roll.bin` stripped from the container → `read_mu` raises (required
    member missing), the unpack stage never runs.

`seed.bin` is a required S5 member but not the seam under test; the real
`seeds/bwv227.1.seed.yaml` bytes stand in.

## Placement note

The issue suggested `tools/muse_pack/tests/`; S2 landed as
`tools/muse_roll/`, so the suite lives at `tools/muse_roll/tests/`
(equivalent, per the issue's "or equivalent"). The `muse_roll` suite in
`tools/run_tests.sh` discovers it by directory recursion — no runner or
suite-inventory change.

## Residual gaps (not blocking; candidates for future work)

1. **Beethoven tiers through the container.** W4's pairwise diff exceeds
   budget at B5/B9 scale; the chain harness pins those structurally
   (note-count equality), not by diff. A slow-tier container round-trip
   for B9 would close this.
2. **Real seed encoding in the container.** The seed member is raw yaml
   bytes; once S3/C1 emit a canonical `seed.bin` encoding, the seam test
   should pack a real encoded seed.

## How to run

```bash
cd tools && python -m pytest muse_roll/tests/test_container_seam.py -q
# or the whole gate:
./tools/run_tests.sh
```
