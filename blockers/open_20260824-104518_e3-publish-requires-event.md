# Blocker: E3 — "Published recording" requires the staged event

- **Task:** #211 (E3 — The recording)
- **Filed:** 2026-08-24T10:45Z, run=20260824-1035-3436
- **Status:** `status:blocked-needs-input` on #211

## What was attempted

Claimed #211 and worked both DoD bullets:

1. **"Publication surface chosen per open questions"** — done. The E3
   design doc is promoted scaffold → draft
   (`docs/design/e3-the-recording.md`): two-surface recommendation (event
   film + self-hosted release bundle), release format, the
   provenance-complete `recording_manifest.json` spec (extending the
   `tools/muse_mu` conventions: SHA-256 hashes, HMAC signature per D18,
   `ai_involvement` vocabulary, per-movement live-vs-`.perf` declaration
   carried over from the E2 plan), and a post-event publish checklist.
2. **"Published recording + provenance-complete manifest"** — **not
   achievable by an agent.** There is no staged event: E1's landed work is
   the execution scaffold (the founder's ear-gate has not approved a
   concert-worthy render), and the E2 plan explicitly gates dating and
   contracting the venue on that approval. A recording of an event that
   has not happened cannot be published; closing the issue anyway would be
   a false done.

## What is missing (the decision for the human)

E3 as filed mixes an agent-completable planning deliverable with a
physical-world deliverable. The issue is under-scoped for the current
phase. Recommended split (per TASK_WORKFLOW.md's "recommend splitting"
guidance):

- **E3a — Publication plan** (done in the draft above; can be reviewed on
  dev at 39ffaeb's sibling commit for #211).
- **E3b — Publish the recording** — new task, blocked by the staged event
  (i.e., by the founder's E1 ear-approval + E2 venue contracting). Its
  DoD is the publish checklist in the design doc, executed.

Alternative resolution: the human re-scopes #211's DoD to the plan and
closes it, filing the post-event publish task themselves.

## What was tried and why insufficient

- Checked the queue and `git log origin/dev`: E1 (#200) closed with the
  scaffold; no concert-worthy render, no certified `.perf`, no event
  date. E2 (#210) closed with the event plan; its Timeline-gating section
  states nothing is dated until the founder's ear approves.
- The vision defers streaming/platform decisions past the event, so no
  surface work beyond the plan is executable either.

## Notes

- Status caches updated in the same commit (docs/design/index.md,
  docs/pipeline.md) to show "plan drafted; publish blocked."
- No test spec was filed as a `Tests:` issue (the task is blocked, not
  done); the coherence checks for this doc can reuse the pattern in
  tests/open_20260824-103353_e2-venue-plan.md when E3 resolves.
