# muse_docs — mechanical doc-prose lint (T7, #299)

Deterministic, offline, zero API calls: the agent *is* the prose checker
(that is the checklist convention in [AGENTS.md](../../AGENTS.md)); this is
the cheap mechanical tier that runs in the fast test suite and catches the
drift a reviewer keeps re-finding by hand.

Design: the issue's constraint is explicit — **no external API or model**.
So the split is:

| Layer | Who | What |
|---|---|---|
| Mechanical (this tool) | `run_tests.sh` fast tier | link/path/rename/encoding checks — deterministic, sub-second |
| Prose | the agent's own session | verifiable claims, hollow sentences — the checklist convention |

## Usage

```bash
python3 tools/muse_docs/cli.py lint              # findings; exit 1 if any
python3 tools/muse_docs/cli.py lint --report     # markdown triage report
python3 tools/muse_docs/cli.py lint --kind broken-link
python3 tools/muse_docs/cli.py lint --json
python3 tools/muse_docs/cli.py lint --quiet      # exit code only
```

Exit 0 when clean, 1 when findings exist, 2 on usage errors. Suite:
`cd tools && python3 -m pytest muse_docs -q` (registered in `run_tests.sh`
as a fast-tier suite).

## What it checks

| Kind | Catches |
|---|---|
| `broken-link` | a relative markdown link whose target does not exist (depth errors like `../../FORMAT_SPEC.md` from `docs/`, which escapes the repo root); also a reference-style use with no matching definition |
| `unresolved-ref` | a backticked path naming a live repo path that does not resolve |
| `stale-open-ref` | a reference to an `open_*` record (test spec / bug / blocker) whose file has since been renamed `closed_` |
| `unfilled-template` | a raw `[TODO]` / `TBD` left in a doc |
| `encoding` | a markdown file that is not valid UTF-8 |

### Link forms covered

All three markdown link forms are parsed, so no link escapes checking by
being written unusually (each has a test with a broken target):

| Form | Example |
|---|---|
| inline | `[x](dest.md)` |
| inline + title | `[x](dest.md "Title")` |
| angle-bracketed | `[x](<dest.md>)` |
| reference-style | `[x][label]` + `[label]: dest.md` |

A naive `\[..\]\(([^)\s]+)\)` matches only the first, so a titled or
reference-style broken link used to lint **clean** — a silent hole closed in
#311.

### Resolution semantics

- Paths resolve **relative to the document**, so depth matters
  (`../FORMAT_SPEC.md` from `docs/design/` resolves; `../../FORMAT_SPEC.md`
  escapes the repo root and is flagged).
- Resolution is **case-sensitive**, matching the repo's filesystem: a
  wrong-case link would 404 on a case-sensitive host, so it is flagged.
- **Symlinks are followed** (`os.path.exists`), so a link through one is
  valid.

## Finding budget

`FINDING_BUDGET` (25) is a ceiling: above it the CLI prints an error to
stderr and exits 1. A rule change that starts flagging hundreds of things is
almost always a mis-firing linter, not hundreds of real defects — and the
failure mode it prevents is a flooded queue nobody triages. Raise it
deliberately, in the same commit as the change that needs it, never to make a
red run go green. Override per-run with `--max-findings N`.

## What it deliberately does not check

- **Historical framing.** "the current IR, not the earlier `tools/muse_ir/`"
  is prose about a past state, not drift. A mention preceded by a word like
  *earlier/superseded/removed/renamed* in the same sentence fragment is
  skipped. Force agent authors to delete that framing and the docs lose the
  reasoning they exist to preserve.
- **Prose refs.** Placeholders (`YYYY-MM-DD`, `<date>`), globs (`tests/**`),
  and abbreviated lists (`docs/design/e1..e3`, `seeds/x.v1/v2`) are prose,
  not path claims.
- **Command lines.** `` `tools/muse_seed_cli/cli.py validate` `` truncates to
  the leading path-shaped run; the trailing word is an argument.
- **Archived records.** `tests/closed_*`, `bugs/closed_*`, `blockers/closed_*`
  and `docs/audit/*` describe the world as it was. Moved paths there are not
  drift, and "fixing" them would rewrite history.
- **Superseded docs** listed in [`docs/superseded.txt`](../../docs/superseded.txt)
  (`SCHEMA_SPEC.md` is "design history only").

## Findings are a triaged queue, not a build failure

Per the issue: findings land as `documentation` issues and a
`docs/audit/<date>-doc-prose.md` report; a weekly run is a habit-check. The
suite still fails while findings exist so drift cannot land *silently* — the
fix is to clean the finding or record the exemption, not to skip the test.

```bash
python3 tools/muse_docs/cli.py lint --report > docs/audit/$(date +%F)-doc-prose.md
```

## Findings this tool found on landing (2026-09-16)

26 real findings across 12 files, all fixed in the landing commit:

- 10 READMEs linking test specs by their pre-rename `open_*` name (each
  became `closed_*` when the spec completed) — both the link and the inline
  reference.
- 3 path-depth errors: `FORMAT_SPEC.md` linking `../tools/s1_stream/` from
  the repo root, `docs/pipeline.md` linking `../../FORMAT_SPEC.md` (escaping
  the root), `docs/design/s3-seed-format/SPEC.md` linking
  `../delta-analysis-plan.md` (one level short).
- 1 dead reference to `docs/audio-convention` (the doc is
  `docs/audio/README.md`).
- **1 non-UTF-8 doc**: `docs/design/r1-rehearsal-directives.md` carried a
  mangled em-dash (`0xd1` where `—` belonged, from #283). Invisible in
  review, breaking for editors and agents. Repaired.

## Dependencies

Stdlib only (`glob`, `os`, `re`). No network, no model, no third-party
packages.

## Tests

`cd tools && python3 -m pytest muse_docs -q` — 57 tests, sub-second.

- `tests/test_lint.py` — every check exercised against a synthetic repo in
  `tmp_path` so it is proven to *catch* its drift class; each link form has a
  broken-target case; false-positive guards pinned (prose refs, historical
  framing, archived records, superseded docs); resolution semantics
  (relative-to-document, case-sensitive, symlinks followed); the finding
  budget; and `test_real_repo_has_no_findings` as the regression gate.
- `tests/test_cli.py` — the CLI surface: exit codes (clean 0 / findings 1 /
  `--quiet` silent), `--kind` filtering, `--json` shape, `--report`
  structure, and the budget error landing on stderr rather than stdout.