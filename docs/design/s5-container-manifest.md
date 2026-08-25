# S5 — Container + manifest (design doc, scaffold)

**Phase 1 — Format spec. Status: scaffold.**

## Purpose

Zip layout, plaintext rights manifest (license, provenance, AI disclosure),
content hashes of every member, signature. The manifest is the only human-
readable member — a lawyer reads it with a text editor.

## Dependencies

- **Upstream:** none technical — fields come from FORMAT_SPEC §3.
- **Downstream:** P1 (reading), C4 (writing), and the open `.mu` definition.

## Scope (pin in draft)

- **Inputs:** manifest field set (license enum, provenance, hashes).
- **Outputs:** spec section + manifest validator.
- **Non-goals:** distribution/registry concerns (explicitly not yet).

## Open questions

- Signature mechanism specifics; hash algorithm.

## Acceptance criteria (when promoted to draft)

- Spec section written; validator accepts/rejects example manifests
  correctly.

## Event log (implementation, 2026-08-23)

- Spec landed as FORMAT_SPEC §7.1 (v0.x addition, per the changelog rule).
  Validator + container toolkit: `tools/muse_mu/manifest.py`.
- Decisions: SHA-256 for member hashes; signature = optional HMAC-SHA256
  over canonical JSON (minus the signature field); PKI deferred.
- Provenance field set mirrors the S3.3 philosophy provenance where they
  overlap (author, license_ref) plus the manifest-only `ai_involvement`
  enum (none|assisted|generated), `source`, `tools` — the §3 draft's
  "source, tools, AI involvement disclosure" concretized.
- **Lineage fields (S5.1, 2026-08-25, #249):** `extends`/`operation`
  joined `PROVENANCE_KEYS` (optional, validated — `extends` reuses the
  `_validate_hashes` digest check, now shared as `is_sha256_hex()`). The
  mirroring rule above is the sync mechanism: at pack time the manifest's
  `extends`/`operation` are copied from the packed seed's provenance
  (S3.7, #248) — the seed file is the source of truth, the manifest
  restates it.
