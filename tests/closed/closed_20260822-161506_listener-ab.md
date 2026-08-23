# Test spec — Listener MVP 3 #99: A/B rendition switch

**Source task:** #99 (both renditions pre-rendered; crossfade at current
playback position)
**Code under test:** `explorer/src/listen/crossfade.js`,
`explorer/src/listen/ListenTab.jsx` (switchRendition, prerender cache).

Coverage landed with the task: `explorer/src/listen/crossfade.test.js` —
11 vitest checks (position ⇄ bar mapping incl. compound meter + fallback,
equal-power gain law incl. constant total power + clamps, switch planning
across tempos) plus a browser pass: play Midnight Drive → switch to Late
Set mid-playback — position mapped across the tempo change (0:19 in,
§ verse.1 preserved), crossfade overlap, no re-expansion at switch time.
This spec is for what remains.

## Residual coverage landed (closed by #103, 2026-08-22)

Pinned in `explorer/src/listen/crossfade.test.js` (4 new checks, 77/77 green):
exact integer-bar seam mapping, zero-position invariance, past-end passthrough
(clamping is the transport's job), and A→B→C→A multi-hop bar preservation
(the third-rendition cycling pin, at the math level).

Deferred (UX/player-level, not unit-pinnable): true GainNode automation
ramps, switch-while-paused behavior, and switch-spam queueing — those need
component-level tests against ListenTab's timers, not pure math.

## Behaviors to verify (original spec — covered or deferred above)

- **True gain-node crossfade:** MVP uses timed pause/overlap, not actual
  gain ramps on the audio path — a follow-up should route both transports
  through GainNodes and apply crossfadeGains as scheduled automation.
  Pin: during a fade, ctx gain automation events exist for both nodes.
- **Switch while paused:** currently requires playing state implicitly;
  pin behavior (switch allowed from pause, resumes at mapped position or
  stays paused — UX decision).
- **Switch spam guard:** rapid switches during a fade — the `fading`
  flag blocks; pin the queue/reject behavior.
- **Position mapping at section boundaries:** switching exactly on a
  section seam — bar mapping is continuous; pin no off-by-one at integer
  bar positions.
- **Third+ rendition cycling:** switch works across all three full-example
  renditions (Chamber included) — browser pass covered two; extend.

## How to run

`cd explorer && npm test` (vitest); browser pass in the closing note.
