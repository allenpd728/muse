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

## Residual coverage this follow-up must add

- **CI green run:** `.github/workflows/ci.yml` is committed but cannot go
  green until `package-lock.json` is committed (#31 — `npm ci` requires it).
  Verify the first green run on `dev` and record the run URL here.
- **CI trigger check:** confirm the workflow fires on push to `dev` and on
  PRs (open a no-op PR or inspect the Actions tab).
- **Sidecar channel pinning** (see above).

## How to run

`npm test` locally; CI runs the same on push to `dev`.
