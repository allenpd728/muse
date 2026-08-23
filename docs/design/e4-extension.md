# E4 — Extension decision (design doc, scaffold)

**Phase 5 — The event (sub-task). Status: scaffold.**

## Purpose

`.mu` collides with Kerbal's model format and the `mu` Lisp toolchain
(documented in [../delta-analysis-plan.md](../delta-analysis-plan.md)).
This sub-task decides the final extension — `.mu`, `.muse`, `.muw`, `.egg`
— before spec publication, updates spec/corpus/tooling, and clears the
launch gate.

## Dependencies

- **Upstream:** founder decision (input); S5 (container mechanics as the
  landing surface).
- **Downstream:** S5, publication.

## Scope (pin in draft)

- **Inputs:** name candidates + collision evidence.
- **Outputs:** chosen extension + updated docs/spec/corpus/tooling.
- **Non-goals:** branding beyond the extension (project name stays "Muse").

## Open questions

- `.mu` vs `.muse` vs `.muw`; final record in this doc + FORMAT_SPEC §3.

## Acceptance criteria (when promoted to draft)

- Decision recorded; spec/corpus/tooling updated to the chosen extension.
