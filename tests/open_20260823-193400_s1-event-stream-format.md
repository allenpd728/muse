# Test spec — S1 event-stream format (task #137)

Written 2026-08-23 by the completing agent, per TASK_WORKFLOW §6.

## Status of coverage

S1 shipped with 6 pytest tests in `tools/s1_stream/tests/test_golden.py`,
all passing (~10 s):

- canonical form is deterministic and byte-stable across parses
- canonical structure pins (meta, maps, parts, note fields, notations)
- verify round-trips (Byrd MIDI path)
- tampering detected (pitch mutation → verify FAIL)
- dynamics + hairpin serialization (Beethoven 5: 431 dynamics)
- unpitched percussion preserved (Beethoven 9: 835)

Plus the committed golden vectors in `tools/s1_stream/golden/` (4 works,
regenerated and verifiable via W4).

Run: `cd tools/s1_stream && python -m pytest` (<60 s).

## Behaviors still needing coverage (gaps)

1. **Verify-as-CI-gate.** The `verify` command's exit codes are tested in
   pytest but not wired to a CI workflow; when CI returns (AGENTS.md
   Build/test), `muse_stream.golden verify` against every committed
   vector must gate every change to tools/ir.
2. **Beethoven 9 + Byrd full-corpus golden coverage.** Vectors currently
   cover 4 of 5 works (and 1 of 6 Byrd movements). At ~2–4 MB per
   orchestral vector, ship-and-pin all 5 works + Byrd 6-movement set is
   fine; do it and pin sizes in this spec's replacement.
3. **P3 decoder contract.** The golden verifier pins (source → canonical
   JSON). P3's actual conformance gate is (`.mu` → event stream); when P1
   lands, the golden vectors become its vectors' source side — a round-
   trip test (encode → P1 decode → canonical JSON == golden) belongs in
   P3's spec, not here.
4. **Schema stability guard.** The canonical JSON is a contract; an IR
   change that renames/moves a field must fail golden verification loudly.
   A negative schema test (drop a required field → verify FAIL, not KeyError)
   would pin this better than tamper-by-value.
5. **Formatter drift guard.** Python's json.dumps separators guarantee is
   fine today; pin `canonical_json` against a hand-written expected prefix
   so a future formatting change can't slide under the verify gate.

## Invocation

`cd tools/s1_stream && python -m pytest` (~10 s).
