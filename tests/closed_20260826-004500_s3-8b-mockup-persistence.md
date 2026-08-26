# Test spec — S3.8b mockup persistence + distiller stamping (task #254)

Written 2026-08-26 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

`tools/muse_distill/distill.py`: `seed_revision(mockup, mockup_path=None)`
— `provenance.operation: muse_distill@1` always; `extends` = SHA-256 of
the persisted mockup's bytes when `mockup_path` is given.
`tools/muse_grow/grow.py`: `persist_mockup(mockup, out_path,
seed_path=None)` — writes the mockup (via `dump_mockup`) carrying
`provenance.seed_hash` (the driving seed's bytes hash); `grow_one` gains
`mockup_out`/`seed_path` kwargs and persists before distilling so
`extends` names committed bytes. `tools/muse_grow/cli.py`: `--seed` /
`--mockup-out` flags. First live 3-hop chain committed:
`seeds/bwv227.1.v3.seed.yaml` → `bwv227.1.v2.mockup.json` →
`bwv227.1.v2.seed.yaml` → root (all verified by `muse_lineage`).

## Coverage to write

Extend `tools/muse_distill/tests/` and `tools/muse_grow/tests/`, run with
`cd tools && python -m pytest muse_distill muse_grow -q`.

1. **Stamping.** `seed_revision` without `mockup_path` → `operation`
   present, `extends` absent (backward compat); with `mockup_path` →
   `extends` equals the file's SHA-256 (use `tmp_path`).
2. **Persist shape.** `persist_mockup` output parses as JSON, carries
   `provenance.seed_hash` matching the seed file's bytes, and validates
   against `muse_mockup.schema.validate_mockup_schema` (the L1.10
   contract — the seam where schema and persistence meet).
3. **End-to-end chain (known-answer).** Fixture or the committed chain:
   `walk(seeds/bwv227.1.v3.seed.yaml)` is 4 hops, all verified/root —
   drift here means a link broke; re-stamping must be deliberate.
4. **CLI seam.** `muse-grow <work> --seed <s> --mockup-out <m> --out
   <d>`: the mockup file exists, the delta's `extends` matches it, and
   omitting `--mockup-out` produces a delta with no `extends` (old
   behavior preserved).
5. **Operation tag precedence.** A seed with its own
   `provenance.operation` still drives the G4 `expansion.operation`
   (sibling behavior — pin that #254 didn't disturb it).

## Known gaps (acceptable)

- Mockups are regenerated per iteration (stand-in is deterministic), so
  re-running grow overwrites the file byte-identically; a real-L1 future
  makes mockup bytes non-deterministic — the commit-per-iteration
  discipline becomes load-bearing then, and is a human/loop concern, not
  a testable one here.

## Closed 2026-08-26 (#262, run=20260825-1033-cae1)

Distill (test_distill.py, +2): stamping omitted without mockup_path
(backward compat: operation stamped, extends absent); extends == SHA-256
of the persisted file's bytes.

Grow (test_grow.py, +5): persist shape (seed_hash of the driving seed's
bytes; dataclass-dump shape pinned — the L1.10 session-file schema does
NOT apply here, spec item 2 corrected with a flip-test); seed_hash
omitted without --seed; the committed 3-hop chain known-answer pin
(v3 → v2.mockup → v2 → root, [verified, verified, verified, root]);
CLI seam (--seed/--mockup-out end-to-end, extends matches persisted
bytes; omitting --mockup-out preserves the old no-extends behavior);
G4 operation-precedence pin (seed's own provenance.operation wins).

Suites: muse_distill + muse_grow → 30 passed, 0 skipped.
