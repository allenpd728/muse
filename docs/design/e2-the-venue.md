# E2 — The venue (design doc, draft)

**Phase 5 — The event. Status: draft (event plan, issue #210).**

## Purpose

Concert hall, projection, the "giant computer" staging — the public
performance as event. Precedent: Illiac Suite (1957), Gould/Bernstein
(1962). The question "can a machine conduct Beethoven?" fills seats.
The controversy is the coverage; the hall is where the argument happens.

## Dependencies

- **Upstream:** E1 (something worth staging — one founder-approved,
  concert-worthy render + its certified `.perf`).
- **Downstream:** E3 (what gets recorded; this plan must not preclude it).

## Scope

- **Inputs:** E1's approved render + certified `.perf`, venue options.
- **Outputs:** this event plan — venue option, staging mechanics for live
  LLM deliberation, projection design, rights/provenance posture.
- **Non-goals:** broadcast/distribution (E3), ticketing operations, venue
  contracting and dating (founder action once E1's ear-gate passes).

## The event concept

One evening, one question, staged as an argument in three acts:

1. **The soil.** The deterministic player performs the work from the score
   alone — correct, identical everywhere, forever. The audience hears the
   root system: this much is settled mathematics.
2. **The deliberation.** The house lights stay low; the machine takes the
   stage. The LLM player reads score + prompt and prepares its performance
   live, in full view. Minutes of deliberation are the feature — the
   audience watches interpretation happen.
3. **The bloom.** The LLM player's performance, heard against the memory
   of act 1. Same score, same sanctions, a reading. The Gould/Bernstein
   case restaged with the machine as conductor: the disagreement *is* the
   program.

The `.perf` certified render is the safety net, never the show: if live
deliberation overruns its window for a movement, that movement is heard
from the certified render and the live trace keeps running on the
projection — labeled on screen as which is being heard. Honesty about
what is live is part of the work's provenance ethics.

## Venue option

Recommendation: **a university-affiliated concert hall or science-museum
hall, 300–500 seats, with a real projection surface and house recording
capability.**

Decision criteria, in order:

1. **Acoustic honesty.** A hall built for unamplified chamber/orchestral
   sound, so the rendered performance (via a high-end house PA or
   spatialized speaker array) is judged fairly against the audience's
   memory of live players.
2. **The machine reads as instrument, not gadget.** Sightlines that let a
   visible compute rack + projection live on stage without displacing a
   (symbolic) conductor's podium. Museum/science-center halls score well
   here — the Illiac precedent puts the machine at center stage.
3. **The audience is the argument.** A university music + CS community
   guarantees the Gould/Bernstein dynamic: critics, students, and
   practitioners who will disagree in public afterward.
4. **Recording rights in the standard agreement.** The venue contract must
   permit house audio/video recording and downstream publication (E3) —
   a hard requirement, checked before signing.

Alternatives considered: a traditional big-hall stage (better prestige,
worse sightlines for the machine, harder recording terms) and a black-box
theater (best staging control, weakest acoustic framing for the
"concert" claim).

## Staging mechanics for live LLM deliberation

The open question, answered. The problem: the LLM player is slow by
design — deliberation is measured in minutes, and dead air kills a hall.
The mechanics turn the latency into the spectacle:

- **The machine on stage.** A visible, lit compute rack (the "giant
  computer") downstage of a projection scrim. Its status lights are the
  only moving scenery. No attempt to hide it: the machine is the
  performer.
- **Pacing by ladder, not by symphony.** Program the evening short-to-
  long along the corpus ladder's spirit: a Bach chorale-scale opening
  (deliberation window ~2–3 minutes, tolerable raw), then longer forms as
  the audience learns how to watch. The headline work comes last, when
  watching deliberation is itself the learned skill of the evening.
- **Deliberation windows are scored.** Each movement has a planned
  deliberation window, announced in the program like a tempo marking.
  During a window, the projection (below) carries the hall; a narrator/
  dramaturg voice reads the trace highlights — "it is re-weighing the
  subito piano against the seed's stated philosophy" — the way a radio
  broadcaster narrates a chess move.
- **Overlap mechanics.** Deliberation for movement N+1 begins as movement
  N sounds, when the pipeline allows; the audience sees both clocks.
  Where overlap is impossible, intermissions are programmed at movement
  boundaries rather than forcing continuous attention.
- **The narrator.** A human dramaturg (founder or designate) frames each
  act and narrates trace highlights. This is presentation, not
  interpretation — the reading belongs to the machine and the seed.

## Projection design

Three layers, one scrim, in plain sight — the audience should be able to
audit the performance while it happens:

1. **The score.** The work as notation and/or piano-roll (W5 renders),
   tracking the playback position. During act 1 this is the whole frame.
2. **The seed.** The prompt's declared philosophy and sanctioned ranges,
   shown as data: what may vary, and what the work forbids. Projected
   before the LLM performance so the audience knows the rules the machine
   is playing inside.
3. **The live trace.** The deliberation log as it is produced —
   parameters under consideration, options weighed, decisions committed —
   rendered for a lay audience (trace highlights, not raw logits).

Opening ritual: **the manifest is projected and read before any music.**
Rights are plaintext by design (FORMAT_SPEC §3); the event makes reading
the label part of the ceremony — work, source, license, AI involvement,
hashes on screen.

## Provenance + rights posture

Per manifest conventions (FORMAT_SPEC §3, `tools/muse_mu/manifest.py`):

- **Corpus is public domain.** The score carries no performance-rights
  encumbrance; the event's claim is about interpretation, not ownership.
- **The seed is human-authored or human-approved.** Any AI involvement in
  the staged `.mu` is declared in the manifest
  (`ai_involvement: assisted | generated`, with `tools` listed) — the
  disclosure is part of the show, not fine print.
- **No artist lookalikes.** Prompt philosophies staged at the event
  reference styles and practices, never an artist's identity, absent an
  explicit license in the manifest.
- **The `.perf` is labeled.** Any moment the hall hears the certified
  render instead of a live deliberation is labeled as such on screen —
  provenance applies to the evening, not just the file.
- **Venue agreement must not encumber E3.** Recording and publication
  rights retained; audience notice (filming in progress) at doors.
- **Program notes carry the manifest in full.** Plaintext rights,
  printed.

## Timeline gating

The event follows E1: nothing here is dated or contracted until the
founder's ear approves a concert-worthy render. Once E1 passes, the
founder's actions are: pick the venue from the option above, date the
evening, sign (checking the recording-rights clause). Everything else in
this plan is executable without further product decisions.

## Open questions

- **On-site vs. remote deliberation compute.** On-site rack maximizes the
  "giant computer" staging but caps model size; remote compute over a
  visible network link is honest if labeled, and scales to the Ninth.
  Decide with L-series maturity data.
- **Narrator: founder or hired dramaturg.** The founder knows the scores;
  a professional narrator sustains a full evening. Rehearsal decides.

## Acceptance criteria

- Event plan committed (this document): venue option, staging mechanics
  for live LLM deliberation, projection design. ✔
- Provenance + rights aspects addressed per manifest conventions. ✔
- Remaining gate (founder): event dated and contracted after E1 approval.
