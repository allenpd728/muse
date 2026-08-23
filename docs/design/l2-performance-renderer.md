# L2 — Performance renderer (design doc, draft)

**Phase 4 — The product. Status: draft.**

## Purpose

Mockup → audio via sfizz + SFZ samples (SSO/VPO tier). The "worth listening
to" bar — the quality gate spike round 2 established. Critical-path terminus
with L1.

## Architecture (draft)

Three tiers in scope; one declares the build:

| Tier | Library | Integration | Quality |
|---|---|---|---|
| **sfizz** | SFZ player (C API + CLI) | primary | SSO/VPO tier — the "worth listening to" bar |
| **FluidSynth** | soundfont fallback | fallback if sfizz unavailable | GM/baseline |
| **Commercial SFZ** | Spitfire/Vienna/Orchestral Tools | event gate (L5 waiver) | concert-hall | 
|(selected by event budget only) |

**Integration shape:** CLI-first (`sfizz_render_in_place` or
`sfizz_process_and_render`). SFZ per instrumentation (violin/cello/viola/
clarinet/etc.). Sample libraries resolved from environment (SSO/VPO) with
fallback to FluidSynth where available.

**SFZ mapping:** per-part program → SFZ program mapping; all parts mapped
or fallback to GM.

## Dependencies

- **Upstream:** L1 (mockups), P2 (baseline renderer to build above).
- **Downstream:** L3 (comparison listening), E1 (the event render).
- **Critical path:** W1 → W3 → S3 → C1 → C2 → L1 → **L2**.

## Scope (pinned)

- **Inputs:** mockup session files (tempo map, note list, curves).
- **Outputs:** WAV renders to the output directory (CLI emits audio).
- **Non-goals:** notation software, video/audio mixing, streaming
  playback (L3 will handle A/B output).

## Open questions (draft-level)

- Split or subgraph: per-part render then sum, or whole-mix render per
  part then sub-graph.

## Acceptance criteria (when promoted to draft)

- Render Bach chorale via SSO strings audibly (not GM-masked).
- FluidSynth fallback when sfizz absent.
- Test spec + CLI exit codes (0 rendered, 1 failure).
