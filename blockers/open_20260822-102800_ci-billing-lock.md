# Blocker — #42 CI verification: account billing lock disables GitHub Actions

**Task attempted:** #42 (Tests: Batch 1 #14 — invalid examples + CI workflow)

## What is done (committed to `dev`, 96bcd82)

- Sidecar channel-of-rejection pinning: every `examples/invalid/*.expected.json`
  now names its channel (`schema` | `refs` | `semantics`); `tools/test.mjs`
  `mustReject` asserts the pinned channel is the first to fire. Local `npm test`
  green (21/21); negative check confirms a flipped channel goes red.

## What is missing

The remaining DoD items are unstartable until Actions works:

- **First green CI run on `dev`**
- **Trigger check (push to `dev` + PR)**

## Root cause (confirmed by repo owner, 2026-08-22)

GitHub UI banner: **"GitHub Actions workflows can't be executed on this
repository. Your account's billing is currently locked. Please update your
payment information."**

The API symptom of a billing lock is exactly what was observed: the workflows
API reports zero registered workflows, and every push produces a synthetic
`startup_failure` run with `path: "BuildFailed"`, empty workflow name, an
orphan `workflow_id`, and zero jobs (5 runs, 2026-08-22T02:20Z–10:20Z).
Repo-side causes were ruled out before the banner confirmed billing: Actions
enabled (`allowed_actions: all`), workflow file byte-valid at the run's head
SHA, permissions toggled off/on via API with no change.

## Needed to unblock

1. Repo owner: https://github.com/settings/billing → update payment method.
   (Billing locks usually come from an expired/declined card; the lock
   persists until a payment method validates, even at $0 spend.)
2. Once unlocked, the residual work is minutes: retrigger by push, record the
   first green run URL in the test spec, verify the PR trigger, rename the
   spec to `closed_*`, and close #42. #41's remaining DoD (lockfile invariant
   enforced by CI) unblocks at the same moment.
