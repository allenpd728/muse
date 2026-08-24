# P3 — Conformance suite (design doc)

**Phase 2 — Deterministic player. Status: implemented (#212 →
[tools/muse_ci](../../tools/muse_ci/)).**

## Purpose

Golden vectors: `.mu` → event stream pairs, run in CI as a merge gate. The
objective definition of "conforming decoder."

## Dependencies

- **Upstream:** P1 (P2 for render smoke).
- **Downstream:** CI gate for everything after P-series lands.

## Scope

- **Inputs:** committed corpus `.mu` containers (W1 → S2 → S5 build).
- **Outputs:** vector store + pytest gate in the fast tier of
  `tools/run_tests.sh` (verify is decode-only, ~2s for all 13 works).
- **Non-goals:** work-conformance (assertions over sanctioned space) — that
  is L1/C4 territory.

## Decisions (resolved at implementation, 2026-08-24)

- **Vector storage format:** binary `.mu` containers committed in git
  (`tools/muse_ci/vectors/`, 272K total for 13 works — S2's zlib columnar
  keeps them small). Regenerated-at-gate-time was rejected: fixed inputs
  pin the *decoder* independently of encoder drift. Regeneration fidelity
  is itself tested (`test_regeneration_reproduces_pin`).
- **Expected-output pin:** sha256 + byte count of the S1 canonical JSON
  (FORMAT_SPEC §4.4) of the decoded Work — not a duplicate copy of the
  42MB canonical JSON store s1_stream already maintains. `cli.py dump`
  reproduces the actual stream for mismatch forensics.

## Acceptance criteria

- Suite runs in CI; gates merges. (Fast tier of `tools/run_tests.sh`;
  server-side gate resumes with #194.)

