# Test spec — Fix #47: cross-ref lint on all reference surfaces

**Source task:** #47 (extend harness cross-ref lint to all reference surfaces)
**Code under test:** `tools/test.mjs` `danglingRefs()`.

Coverage landed with the task: 10 unit checks in `tests/test-harness.test.mjs`
(one per new surface plus resolve/absent-edge cases) and
`examples/invalid/dangling-ids.muse.json` proving all five surfaces end-to-end
via the refs channel. This spec is for what remains.

## Behaviors to verify

- **Kind-narrowing decision (open):** phrase `motifs[]` and `uses[].ref`
  currently resolve against the full material id pool (motifs + themes +
  rhythms), so a phrase referencing a *theme* id resolves. The field
  description says "Motif references" — decide whether kind-narrowing is a
  lint rule (theme id in a motif position flagged) or the pool convention
  stays. Pin either way with a test; flagging kinds is a new semantic rule,
  deliberately not bundled into #47.
- **Duplicate section ids:** `sectionIds()` is a Set — two sections sharing
  an id make refs to that id resolve. form-semantic checks may already flag
  duplicate section ids (see `tests/form-semantic.test.mjs`); if so, pin
  that the lint relies on it, otherwise consider a lint rule.
- **baseRef on non-string refs:** `uses[].ref` failing schema (e.g. a
  number) hits `String(ref)` in `baseRef` — no crash, but the path report
  shows the stringified value. Pin no-crash behavior.
- **register/tempo_lock keys are not transform-stripped:** keys are plain
  ids by construction (object keys); a key literally containing `#` dangles
  unless an id contains `#` (ids are dotted slugs per §2.8, so `#` never
  appears). Pin with a test.

## How to run

`npm test`; unit checks into `tests/test-harness.test.mjs`.
