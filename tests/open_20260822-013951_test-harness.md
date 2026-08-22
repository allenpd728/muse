# Test spec — Batch 1 #3: test harness

**Source task:** #3 (test harness: examples + negative tests + cross-ref integrity)
**Code under test:** `tools/test.mjs` — `danglingRefs()` and the valid/invalid
example loops; `tools/fixtures/*.muse.json` as self-tests.

The harness self-verifies on every `npm test` run (fixture check 3 goes red if
dangling refs stop being detected), but `danglingRefs()` itself has no
unit-level coverage. That is what this spec fills in.

## Behaviors to verify

- `form.sections[].uses[].ref` resolves against motif/theme/rhythm ids;
  transform suffixes (`motif.a#seq(+2)`) strip to the base id before lookup.
- `form.sections[].harmony` (string) resolves against
  `material.harmony.progressions[].id` only — a ref to a motif id must dangle.
- `constraints.must_contain[]` resolves against material ids.
- Docs missing `material`/`form`/`constraints` sections: no crash; only present
  sections are checked.
- Entries without `id`, `uses` entries without `ref`, sections without
  `harmony`: skipped, not flagged.
- Invalid-example rejection: a file in `examples/invalid/` is rejected when it
  fails schema validation **or** has dangling refs (either channel alone
  suffices). Unparseable JSON also counts as rejected (CLI exit 1).
- `.expected.json` sidecars: every `messages` substring must appear in the
  combined error output, or the case fails.

## Edge cases

- Ref equal to a progression id used in `uses[].ref` — currently resolves
  (progressions are material); decide and pin whether that should dangle.
- `harmony` value that is an object, not a string — currently skipped.
- Empty `sections: []`, empty `must_contain: []` — no dangles reported.
- Ref with multiple `#` separators (`x#inv#seq(+2)`) — base id is the first
  segment; pin that behavior.

## How to run

`node tools/test.mjs` today; the follow-up tests can either export
`danglingRefs()` from `tools/test.mjs` for direct unit tests, or drive the
harness end-to-end with crafted fixture/example directories in a temp dir and
assert exit codes. Either shape lands under `npm test`.

## Notes

The harness intentionally spawns `tools/validate.mjs` as a child process so the
CLI contract (exit codes, `valid:`/`invalid:` output) is exercised by the same
suite — tests written for #26's spec should slot into the same loops.
