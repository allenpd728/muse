# L2 — Performance renderer (design doc, scaffold)

**Phase 4 — The product. Status: scaffold.**

## Purpose

Mockup → audio via sfizz + SFZ samples (SSO/VPO tier). The "worth listening
to" bar — the quality gate spike round 2 established. Critical-path terminus
with L1.

## Dependencies

- **Upstream:** L1 (mockups), P2 (baseline renderer to build above).
- **Downstream:** L3 (comparison listening), E1 (the event render).
- **Critical path:** W1 → W3 → S3 → C1 → C2 → L1 → **L2**.

## Scope (pin in draft)

- **Inputs:** mockup session files.
- **Outputs:** WAV renders at sample tier.
- **Non-goals:** commercial-library tier (event decision, deferred),
  notation software.

## Open questions

- sfizz integration shape (CLI vs. library); SFZ mapping per corpus
  instrumentation.

## Acceptance criteria (when promoted to draft)

- Renders a full mockup audibly; passes founder's by-ear bar on one corpus
  work.
