# Blocker — E3 cannot start: no staged event exists to document

**Task:** #211 (E3 — The recording)
**Run:** 20260824-1032-xjzf, 2026-08-24

## What is missing

The design doc (docs/design/e3-the-recording.md, scaffold) states the
input is **"the staged event."** No staged event exists. E2 (#210) landed
as a *plan* — docs/design/e2-the-venue.md plus a test spec — not a staged
performance. There is no event artifact anywhere in the repo or referenced
externally that a recording could document. The Definition of Done
("published recording + provenance-complete manifest") therefore has no
input to satisfy: an agent cannot document an event that has not occurred.

Second gap: the DoD requires "publication surface chosen per
docs/design/e3-the-recording.md open questions," and that doc lists
"Publication surface (release format)" as an open question. Choosing where
the work is *published* is a human decision (audience, licensing exposure,
platform) — exactly the class of call the blocker mechanism exists for.

## What is needed to unblock

1. The event itself: E3 becomes startable only after the staged
   performance E2 planned actually happens (or the human redefines E3's
   input — e.g. a synthetic/mock performance render, which would be a spec
   amendment to the design doc, not an agent's call).
2. A human decision on the publication surface (recorded in
   docs/design/e3-the-recording.md, promoting it from scaffold).

## What was tried

Read the E3 design doc, the E2 deliverables on dev (39ffaeb,
docs/design/e2-the-venue.md — a staging plan, not an event), and searched
the repo for any event/recording artifact. None exists. This is a missing
*decision + real-world input*, not an implementation mechanism, so it is
filed rather than guessed.
