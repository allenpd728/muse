# Test spec — S5.1 manifest provenance lineage fields (task #249)

Written 2026-08-25 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

`tools/muse_mu/manifest.py`: `PROVENANCE_KEYS` += `extends`, `operation`
(both optional). `extends`, when present, validated by the new
module-level `is_sha256_hex()` — the same check `_validate_hashes()` now
uses for member digests (extracted, not duplicated). `operation`, when
present, must be a string. Spec note: `docs/design/s5-container-manifest.md`
event log ("Lineage fields (S5.1, 2026-08-25, #249)") — pack-time copy
rule from the packed seed's provenance.

## Coverage to write

Target file: `tools/muse_mu/test_manifest.py` (extend in place), run with
`cd tools && python -m pytest muse_mu -q`.

1. **Acceptance.** Manifest validates with: no lineage fields; `extends`
   only; `operation` only; both. `to_dict`/`from_dict` round-trip
   preserves them (check whether `provenance` passes through verbatim —
   pin whatever the actual behavior is).
2. **`extends` rejection.** Short/long digest, non-hex chars,
   `sha256:`-prefixed (prefix is NOT the convention — pin), non-string.
3. **`operation` rejection.** Non-string values (int, list).
4. **Unknown-key guard unchanged.** A manifest with an unrecognized
   provenance key still fails — the frozenset grew by exactly two keys.
5. **`is_sha256_hex` parity.** The provenance-`extends` check and the
   member-hash check accept/reject identically across a shared matrix of
   inputs (this is the regression pin for the extraction).
6. **Container seam.** `write_mu`/`read_mu` round-trip a manifest
   carrying both fields; tampered `extends` in a repacked manifest is
   caught by the usual member-hash mismatch (manifest.json hash changes).

## Known gaps (acceptable)

- Verifying that `extends` matches a real parent artifact is S3.8a
  (#251) — chain-walk, out of scope here.
- Nothing currently *writes* manifest-level `extends` at pack time (no
  pack CLI reads seeds yet); the copy rule is spec'd but has no call site
  to test until one exists.
