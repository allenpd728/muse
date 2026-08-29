# Test spec - F3 form-curve structural assertion (#298

Written 2026-08-29 by the completing agent, per TASK_WORKFLOW 6.
Work under test: FORMAT_SPEC 5.1 assertion-kind note + tools/muse_assert
README table row + asserts.py wiring + tests.

## Behaviors to verify

1. **Spec note**: FORMAT_SPEC 5.1 (S3.5 assertion vocabulary)
   mentions `form_curve_correlation` and links tools/muse_assert README.

2. **README row**: kind shape `{letters: [...], window_beats?: int}` with
   semantics: declared form-letter run appears as a contiguous subsequence
   of the derived form curve (A/B/C letters via muse_form).
3. **Wiring**: validate_assertions dispatches `form_curve_correlation` to
   `_check_form_curve_correlation`; unknown kinds still rejected; empty
   letters no-op; lazy import keeps unused path light.

4. **Deterministic test vector**: isochronous repeated monophonic C4 over
  16 notes yields a stable  8-window all-A curve (`AAAAAAAA`); declared
   `[A,A]` and 8x`A` pass; `[B,B]` and `[Z]` fail with kind;
   `window_beats` override accepted.



## How to invoke

```bash
cd tools && python3 -m pytest muse_assert -q
```

Gate evidence (from completing agent: `./tools/run_tests.sh --jobs 1`
-> all suites green (muse_assert 23 passed (was 18;; docs 12 passed;
muse_form 5 passed)).



## Deliberately not covered

The optional distill/compare correlation metric (design-doc row F3) is
explicitly deferred (scope-trim note on #298; would be its own task).
Live form-curve behavior across the corpus (e.g. Beethoven 5 letter-sequence eyeball) is
human-evaluation terrain (per F1 design; not a CI pin).

## Closed 2026-08-29 (#302, run=20260829-0246-439d)

Confirmed green on current dev state (HEAD cb135e0, 2026-08-29):

1. **Spec note**: FORMAT_SPEC 5.1 lists `form_curve_correlation`and links
   the muse_assert README (grep-confirmed, FORMAT_SPEC.md line 259)。
2. **README row**: kind shape `{letters: [...], window_beats?: int}` present with
   derived-curve semantics(tools/muse_assert/README.md line 24)。
3. **Wiring**: `TestFormCurveCorrelation` covers dispatch/fail-loud/no-op/lazy-import
   path — 5 deterministic tests in `tools/muse_assert/test_asserts.py` (landed
   with #298)。
4. **Gate**: `./tools/run_tests.sh --jobs 1` -> all suites green (muse_assert 23
   passed, docs 12 passed, muse_form 5 — matching the completing agent's
   evidence)。

The follow-up's scope was confirm-the-suite-stays-green on current dev state; the
optional distill/compare correlation metric and live corpus form-curve eyeball remain
deliberately deferred(per the spec's not-covered section; human-evaluation terrain)。
 No new test code needed。

_This spec was filed by an AI agent(OpenHands) on behalf of the repository owner._
