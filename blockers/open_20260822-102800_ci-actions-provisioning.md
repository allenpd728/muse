# Blocker — #42 CI verification: GitHub Actions cannot start any workflow (account-level)

**Task attempted:** #42 (Tests: Batch 1 #14 — invalid examples + CI workflow)

## What is done (committed to `dev`, 96bcd82)

- Sidecar channel-of-rejection pinning: every `examples/invalid/*.expected.json`
  now names its channel (`schema` | `refs` | `semantics`); `tools/test.mjs`
  `mustReject` asserts the pinned channel is the first to fire. Local `npm test`
  green (21/21); negative check confirms a flipped channel goes red.

## What is missing

The remaining DoD items are unstartable from inside the repo:

- **First green CI run on `dev`** — impossible: no workflow run can start.
- **Trigger check (push to `dev` + PR)** — impossible for the same reason.

Every push trigger (5 runs, 2026-08-22T02:20Z through 10:20Z, including after
toggling repo Actions permissions off/on via API) completes as
`startup_failure` with `path: "BuildFailed"`, empty workflow name, a
`workflow_id` matching no registered workflow, zero jobs, and no logs. The
workflows API reports `total_count: 0` despite a valid
`.github/workflows/ci.yml` on `dev` (byte-verified at the run's head SHA).

This matches the account-wide GitHub Actions provisioning failure described in
github.com/orgs/community/discussions/202376 symptom-for-symptom (synthetic
BuildFailed runs on all repos of the account, orphan workflow_ids, no jobs or
logs). Repo-side causes are ruled out: Actions enabled
(`allowed_actions: all`), YAML valid, file at the correct path.

## Needed to unblock

Repo owner action, outside agent reach:

1. Check the account-level Actions state (personal account settings →
   Actions; any org policy if applicable), and/or
2. Contact GitHub Support referencing the symptoms above (runs
   32567066425 and 32567340301 are recent examples).

Once Actions can start a run, the residual work is minutes: retrigger by push,
record the green run URL in the test spec, verify the PR trigger, rename the
spec to `closed_*`, and close #42.
