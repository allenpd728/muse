# Test spec — W2 corpus loader (issue #125)

Written by the completing agent per TASK_WORKFLOW step 6. W2 landed with 10
pytest tests (`cd tools/corpus_loader && python -m pytest`, ~21s; the
subprocess CLI tests re-parse the corpus).

## Landed coverage (tools/corpus_loader/test_muse_corpus.py)

- Registry invariant: every corpus file on disk is registered (drift guard).
- `check_file`: green on all 13 files; pin drift and missing files raise
  `CheckFailure`.
- CLI contract (subprocess): `list` enumerates the five works; `load`
  reports parts/notes/maps and marks MIDI sources; unknown work exits 1;
  `check` gate exits 0 with 13 OKs.

## Gaps for the `Tests:` follow-up

1. **Failure-path CLI coverage.** `check` with a corrupted corpus file
   (assert exit 1 + failure list on stderr) needs a fixture corpus; build a
   tmp corpus root rather than depending on the installed one.
2. **Wall-clock budget guard.** `check` re-parses everything (~21s here,
   B9 ≈13s of it). Pin a budget and fail on regression beyond a multiple.
   If it regresses hard, evaluate a cached loader API (`load_work(work_id)`
   returning the Work object) — the design's draft CLI never blocks the
   library form.
3. **Pin provenance assertion.** The pins were measured through `tools/ir`.
   A `check` failure currently says "count drifted" but can't tell parser
   regression from corpus file replacement. Add a `--update-pins` mode that
   rewrites the registry with measured values and prints the diff for human
   review (pins change only by deliberate corpus action).
4. **Warnings contract.** `load` prints parser warnings; assert that
   Schubert's known conflicting-tempo warning is surfaced (currently
   hand-checked), so IR changes don't silently stop surfacing it.

## How to run

```bash
python3 tools/corpus_loader/muse_corpus.py check   # the gate
cd tools/corpus_loader && python -m pytest          # the suite
```
