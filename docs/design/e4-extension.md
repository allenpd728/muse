# E4 — Extension decision (design doc, scaffold)

**Phase 5 — The event (sub-task). Status: scaffold.**

## Decision (locked for development)

**`.mu` is the working extension.** All docs, tooling, corpus references,
and the format spec use `.mu` going forward. This is the development-time
lock; the launch decision remains open.

## Purpose

`.mu` collides with Kerbal's model format and the `mu` Lisp toolchain
(documented in [../delta-analysis-plan.md](../delta-analysis-plan.md)).
For development, the collision is acceptable (nothing public). Before spec
publication, this sub-task reopens: either keep `.mu` (accept collision) or
switch to `.muse`/`.muw` with a migration script. The launch gate is the
decision point, not now.

## Dependencies

- **Upstream:** founder decision at launch (input); S5 (container mechanics
  as the landing surface).
- **Downstream:** S5, publication.

## Scope (pin in draft)

- **Inputs:** launch timing + collision evidence.
- **Outputs:** final extension + migration path if changed.
- **Non-goals:** branding beyond the extension (project name stays "Muse").

## Open questions (deferred to launch)

- Final extension: `.mu` (status quo, collision accepted) vs `.muse` vs
  `.muw`; recorded here + FORMAT_SPEC §3 at decision time.

## Acceptance criteria (when promoted to draft)

- Development uses `.mu` consistently; launch decision recorded with
  rationale and migration path if applicable.
