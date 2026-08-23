# Test spec — Batch 1 #14: invalid examples + CI workflow

**Source task:** #14 (negative-test fixtures + continuous integration)
**Code under test:** `examples/invalid/*.muse.json` + `.expected.json`
sidecars; `tools/semantics.mjs`; `.github/workflows/ci.yml`.

## Behaviors to verify

- Each of the six invalid fixtures is rejected for its stated reason, via the
  harness's `mustReject` loop with `.expected.json` message assertions
  (already live under `npm test` — pinned there on every run):
  - `missing-version` → schema: required `muse_version`
  - `bad-license-enum` → schema: `license.renditions` enum
  - `energy-out-of-range` → schema: `energy` > 1
  - `inverted-tempo-range` → semantics lint (`checkSemantics`)
  - `dangling-material-ref` → cross-ref lint (`danglingRefs`)
  - `named-artist-reference` → policy lint (§2.6 hard rule heuristic:
    "sounds like …" / "in the style of …" phrasing)
- Each fixture fails through **one** channel — a fixture that starts failing
  through a *different* channel (e.g. schema change makes the policy example
  schema-invalid) should be caught in review; consider pinning
  channel-of-rejection in the sidecars (`channel: schema|refs|semantics`).
- The artist-reference heuristic is deliberately narrow (phrase-based). False
  negatives are acceptable (human review remains); false positives on
  technique descriptions (e.g. "sounds like rain") are possible — pin intent
  when the conformance harness lands in Batch 3.

## Residual coverage — outcome (closed by #42, yellow-agent, 2026-08-23)

- **Sidecar channel pinning (done, commit 96bcd82):** all six sidecars carry
  `channel: schema|refs|semantics`; `mustReject` asserts the pinned channel
  fires first. Local `npm test` green (61/61); a deliberately flipped sidecar
  went red and was reverted.
- **CI acceptance rerouted (owner decision, 2026-08-23):** GitHub Actions
  remains disabled by the account billing lock (see
  `blockers/closed_20260823-013100_ci-billing-lock.md`). The CI gate now runs
  inside the Netlify build for `dev`: `netlify.toml`'s command executes
  `npm ci && npm test && npm --prefix explorer ci && npm run test:explorer`
  before building/publishing the dev-- explorer.
  - First gated green build: deploy of commit 8df6909 → `ready` (all suites
    passed before publish).
  - Failed-gate evidence: commit a822ea6 with a deliberately failing explorer
    test → `error`, no publish ("Build script returned non-zero exit code").
  - Trigger check: every push to `dev` fires the gate (the site's allowed
    branch list is `dev`-only; PR builds are off by design).
- If the billing lock ever clears, `.github/workflows/ci.yml` resumes duty
  (a `workflow_dispatch` trigger would need adding first — token-scoped push
  restriction noted on the issue).

## How to run

`npm test` locally (61 suites); `npm run test:explorer` (91 tests). On push to
`dev`, Netlify runs both suites as the publish gate.
