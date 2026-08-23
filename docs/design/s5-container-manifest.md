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
