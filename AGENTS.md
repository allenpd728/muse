# AGENTS.md — Muse

Context and conventions for AI agents (and humans) working in this repository.

## What this project is

Muse is an **executable music format**. A `.mu` file carries three components:
the **score** (the fixed work — our MusicXML-class encoding, packaged), the
**prompt** (the interpretive space — what may vary), and the **manifest**
(plaintext rights). The deterministic player reads the score ("our MIDI
player," the free baseline); the LLM player reads score + prompt and brings
the work to life — slowly, deliberately. A performance is an event, not a
render. The LLM player is **the product**.

See [FORMAT_SPEC.md](FORMAT_SPEC.md) for the format design,
[docs/pipeline.md](docs/pipeline.md) for the build plan and live status, and
[corpus/README.md](corpus/README.md) for the reference works.

> **Development stage: private repo, tools-first.** Nothing is published yet.
> Spec and reference player go public at launch; the **seed workbench
> (C-series) and LLM player (L-series)** stay proprietary.

## Ground rules

- **Format-first.** Never bake musical decisions into a player or tool that
  belong in the format. If a behavior can't be expressed in the spec, amend
  the spec (with a version note), don't hard-code it.
- **Tools before spec freeze.** Phase 0 analysis output drives the language
  design. A construct without corpus evidence doesn't ship.
- **Determinism is the baseline.** The score plays identically
  everywhere, forever. The prompt is where variation lives — never leak
  nondeterminism into the score.
- **The corpus is the ratchet.** Bach → Byrd → Schubert → Beethoven 5 →
  Beethoven 9. Work climbs the ladder; no rung is skipped.
- **No artist lookalikes.** Prompt philosophies reference styles and
  practices, never an artist's identity, without an explicit license in the
  manifest.
- **Provenance is mandatory.** Every `.mu` records source, license, and AI
  involvement in its plaintext manifest.
- **Human evaluation is constant.** The founder knows these scores; every
  render is evaluated by ear against them. Metrics support judgment, never
  replace it.

## Conventions

- **Branching:** `main` is stable; day-to-day work branches from and merges
  into `dev`. Never commit directly to `main`. Name branches for the work
  (`w1-event-ir`, `s3-seed-encoding`) — not `review` or `fix`; the PR is the
  review surface, the branch is just where commits live. Delete branches on
  merge.
- **Task coordination:** per [TASK_WORKFLOW.md](TASK_WORKFLOW.md) — one task
  per GitHub issue, label-based states, blockers over guessing. The standing
  work plan is [docs/pipeline.md](docs/pipeline.md) (W/S/P/C/L task series).
  **One claim per agent at a time** — exactly one `status:claimed` across
  the tracker; finish before claiming the next. Run-ids are mandatory
  (shared GitHub identity makes label/assignee checks useless — the newest
  claim comment's run-id decides ownership), and known-answer tasks close
  only with gate evidence in the done comment.
- **Blockers:** can't start or finish? Write
  `blockers/open_<datetime>_<slug>.md` per the workflow and move on.
- **Tests:** completing a task means spec'ing its tests
  (`tests/open_<datetime>_<slug>.md` + linked `Tests:` issue).
- **Documentation deliverable:** every code task ships a `README.md` in its
  tool directory (usage, API, dependencies) and a test spec in `tests/`.
  The doc is part of the Definition of Done — code without its doc is
  incomplete.
- **Docs coherence sweep:** at session start, check that README, AGENTS,
  FORMAT_SPEC, pipeline, and corpus README agree. A stale doc is a process
  failure on par with a stale claim.
- **Spec edits:** changelog discipline — v0.x may break, v1+ additive only.

## Session lessons (2026-08-23, run=20260823-1945-c7d3)

- **Check for the repo's AGENTS.md before working.** The first session tried
  to act on an empty repo (clone fixed it: allenpd728/muse).
- **The rebase-dedup rule proved itself twice this session** — an S2 codec
  rebase aborted cleanly when a sibling landed first, and seam tests were
  dropped when #165 got claimed by a sibling mid-build.
- **GITHUB_TOKEN can rotate mid-session** — ALL_REPOs_GH_TOKEN works; pass
  it via `GH_TOKEN=$ALL_REPOs_GH_TOKEN gh ...` when plain `gh` refuses.

## Build / test

One command runs the whole repo (issue #167):

```bash
pip install -r tools/requirements.test.txt
./tools/run_tests.sh          # fast tier (~2.5 min, 392 tests)
./tools/run_tests.sh --full   # everything incl. slow suites (~5 min)
./tools/run_tests.sh --list   # suite inventory
```

Per-tool suites live next to their code (`tools/<tool>/test_*.py` or
`tools/<tool>/tests/`); run one with `cd tools && python -m pytest
<suite-dir> -q`. Known-answer pins (corpus counts, golden vectors, W4 diff)
must not drift silently — changing a pin requires amending the source doc
(`corpus/README.md`, FORMAT_SPEC, or the tool's design doc) in the same
commit. CI returns with #163; update this section as tooling lands — do not
leave it stale.

## Repository layout

```
FORMAT_SPEC.md        # format design draft (evidence-frozen at Phase 1)
README.md             # vision + component map
TASK_WORKFLOW.md      # multi-agent claim/work/block protocol
docs/pipeline.md      # build plan + live status (W/S/P/C/L/E series)
docs/vision.md        # product thesis (2026-08-23 revision)
docs/design/          # design-doc scaffolds + dependency index (30 tasks)
docs/decision-log.md  # ADR-style index: locked + open decision points
docs/tech-stack.md    # borrow/build index: software, protocols, specs
docs/literature-review-w1.md  # pre-W1 lit review (IR, compression, patterns)
corpus/               # reference works (Bach, Byrd, Schubert, Beethoven 5+9)
tools/ir/             # W1 event-stream IR + MusicXML/MIDI parsers (pytest suite)
tools/corpus_loader/  # W2 corpus loader CLI (the known-answer gate)
tools/muse_diff/      # W4 IR↔IR diff tool (recall/precision in tick space)
tools/s1_stream/      # S1 golden vectors + verifier (FORMAT_SPEC §4.4)
tools/muse_analyze/   # W3 pattern analyzer → analysis report
tools/muse_viz/       # W5 piano-roll renderer (matplotlib)
tools/muse_roll/      # S2 roll encoding (MUR1 varint columnar + zlib)
tools/muse_mu/        # S5 container + manifest
tools/muse_seed/      # S3 seed format + C1 validator
tools/muse_seed_cli/  # C1 seed CLI
tools/muse_budgets/   # C3 era/style budget engine
tools/assertions/     # C4 per-work assertion sets (S3.5 validator)
tools/muse_ops/       # S4 language validator
tools/muse_assert/    # S3.5 assertions
tools/muse_author/    # C2 AI-assisted authoring
tools/run_tests.sh    # unified test runner (fast/--full/--list)
tools/spike/          # renderer/audio spike scripts (pre-workflow)
SCHEMA_SPEC.md        # SUPERSEDED (JSON-schema v0) — design history only
PRIOR_ART_REVIEW.md   # landscape review (schema-first era)
blockers/             # open_/closed_ blocker reports
tests/                # open_/closed_ test specs (runtime tests live beside the code)
```
