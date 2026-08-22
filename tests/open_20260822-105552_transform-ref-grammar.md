# Test spec — Fix #46: transform-ref grammar on uses[].ref

**Source task:** #46 (enforce the transform-ref grammar on form.sections[].uses[].ref)
**Code under test:** `schema/material.schema.json` `$defs/materialRef`, referenced
from `material.themes[].phrases[].motifs[]` and `form.sections[].uses[].ref`.

Partial coverage landed with the task:
`examples/invalid/bad-transform-ref.muse.json` proves `###garbage` rejection in
both positions via the harness `mustReject` loop; the material suite's existing
transform cases cover the phrase position. This spec is for what remains.

## Behaviors to verify

- Acceptance tables for `uses[].ref`: bare ids of all three material kinds
  (motif/theme/rhythm), single transforms (`#seq(+2)`, `#seq(-1)`, `#inv`,
  `#retro`, `#aug(2)`, `#dim(0.5)`), stacked transforms (`motif.a#inv#seq(+2)`).
- Rejection tables: unknown transform (`#bogus`), malformed args (`#seq(+)`,
  `#aug()`), empty id (`#inv`), leading/trailing `#`.
- Parity pin: the exact same table drives both positions (phrase motifs and
  uses refs) — one shared case list, two assertions, so the grammars can
  never drift apart again.
- `variation` pinned free text: `"developed, ornamented"` and even
  `"developed#aug(2)+orn"`-shaped strings validate in `variation` (it is NOT
  checked against the transform grammar — spec §2.4 sentence).
- Cross-file `$ref` integrity: `form.schema.json` compiled standalone resolves
  `material.schema.json#/$defs/materialRef` (covered by the `addSchema`
  pre-register in `tests/form.test.mjs`; keep wired).

## How to run

Fold into `tests/form.test.mjs` (uses-ref tables) and
`tests/material.test.mjs` (shared case list); `npm test`.
