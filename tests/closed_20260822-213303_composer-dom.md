# Test spec — #116: composer shell DOM mount safety

**Source task:** #116 (DOM-level mount coverage for the composer)
**Code under test:** `explorer/src/composer/main.jsx` (mount),
`explorer/src/composer/mount.test.jsx`.

Coverage landed with the task: `explorer/src/composer/mount.test.jsx` — 3
vitest checks (import mounts into #root in jsdom without throwing, minimal
doc graph round-trip at the data layer, inspector scalar edit recompiles
through graph.mjs). jsdom added as a devDependency (the DOM-renderer
decision deferred from #93–#96 — this issue made it). jsdom gaps stubbed:
ResizeObserver, SVG globals. This spec is for what remains.

## Behaviors to verify

- **Component-level interaction:** the jsdom mount currently asserts
  render + data layer; a user-event simulation (click a node, type in the
  inspector) would pin the React event path — needs
  `@testing-library/react` or a hand-rolled dispatch; decide and pin.
- **Listener DOM mount:** `explorer/src/listen/` components have no DOM
  coverage either — same jsdom pattern applies (AudioContext stubbed).
- **Explorer main app mount:** `explorer/src/main.jsx` (the read-only
  app) — same mount-guard pattern should be pinned.

## How to run

`cd explorer && npm test` (vitest).

---

## Closed — 2026-08-22 (issue #118)

Coverage landed: `explorer/src/composer/interact.test.jsx` — 1 full
interaction scenario in jsdom (React 18 `act` + real event dispatch):
load the full example via the button, click the verse.1 section node in
the canvas, assert the inspector shows its scalar fields (bars = 16),
edit bars to 24 through the input — the edit flows through
applyGraph → compile. No @testing-library dependency; hand-rolled
dispatch (the value-setter trick for controlled inputs).

Deferred (still open, with triggers):

- **Listener DOM mount** — `explorer/src/listen/` components need the
  AudioContext stub; same jsdom pattern applies.
- **Explorer main app mount** — the read-only app's mount guard should
  get the same pin.

Run: `cd explorer && npm test` (91/91).
