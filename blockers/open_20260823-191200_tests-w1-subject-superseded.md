# Blocker — Tests: W1 (#124): subject package is being superseded in flight

**Task attempted:** #124 (Tests: W1 — Event-stream IR), claimed
2026-08-23T19:02Z.

## What is missing

Not information — a stable target. #124's spec
(`tests/open_20260823-190000_w1-event-ir.md`) calls for unit tests against
`tools/muse_ir/`. While the tests were being written, issue #128
(priority:high, claimed by another agent at 18:59Z) filed a retrospective
review finding that `tools/muse_ir/` does not meet W1's DoD (empty MusicXML
maps, no dynamics, key-mode loss, silent drops) and is **landing a
superseding implementation at `tools/ir/` that removes `tools/muse_ir/`** —
with its own 54-test suite and test spec.

Writing #124's tests against a package that is being deleted in flight
guarantees dead work and a rebase conflict with the priority task.

## What I did before blocking

- Confirmed #128's findings independently by running the landed code:
  MusicXML maps empty (Bach mvt 7: `[]/[]/[]` + warning), grace notes present
  but unflagged (512 in Schubert), ties preserved correctly (940/940).
- Filed #129 with the full gap list, then closed it as duplicate once #128's
  overlap was read.
- Left a claim comment trail on #124.

## Needed to unblock (human decision, either suffices)

1. **Close #124 as moot** if #128's shipped test suite covers its spec, or
2. **Re-scope #124** to the new package (`tools/ir/`) once #128 lands — the
   spec's section-1 model invariants remain valid test targets, and any
   coverage #128's suite lacks (per its own test spec) becomes the new
   scope.

Once #128 lands, an agent sweep can resolve this blocker by comparing the
two test specs and acting on the human's call.
