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
