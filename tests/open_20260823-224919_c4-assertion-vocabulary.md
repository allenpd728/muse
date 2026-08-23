# Test spec — C4 assertion vocabulary (task #182)

Written 2026-08-23 by the completing agent, per TASK_WORKFLOW §6.

## Status of coverage

6 pytest tests in tools/assertions/tests/test_vocabulary.py, all passing:

- Both authored sets exist (BWV227.1, Schubert D.810)
- Each validates cleanly through S3.5's validator on its own source
- Out-of-register assertion fails loudly (Bach tight bound → AssertionError)
- Compliant pass is silent
- Unknown work id → empty dict (soft unconstrained)

Run: `cd tools/assertions && python -m pytest` (~1 s).

## Behaviors still needing coverage (gaps)

1. **must_contain and form kinds unpinned in authored sets.** Authored
   sets leave must_contain/form as empty lists (only register/tempo are
   pinned); the vocabulary supports them but per-work themes/sections are
   a human-authoring step. When the founder authors them, extend the pins.
2. **Per-work assertions should be authoried per movement.** Only one
   Bach movement (BWV227.1) and one Schubert file pinned; the corpus's
   other three Bach movements and six Byrd movements don't have sets yet.
   Authoring them is the follow-up.
3. **W3 report integration.** Form invariants could be derived from
   W3's per-work stats rather than hand-authored — when a theme-library
   materializes, pin W3-driven form bounds per corpus tier.
4. **Violation-article diagnostics.** `AssertionError.kind` carries the
   kind; a violation-report formatter (part, note, bound) would make
   founder triage faster. If added, pin its output contract.

## Invocation

`cd tools/assertions && python -m pytest` (~1 s).
