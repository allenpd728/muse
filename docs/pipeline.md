# Muse build pipeline — work plan and status

The single source of truth for what gets built, in what order, and where it
stands. One task = one GitHub issue, per [TASK_WORKFLOW.md](../TASK_WORKFLOW.md).
Status column is updated by the docs-coherence sweep duty.

## Locked decisions

- **Three-component format.** `.mu` = score (fixed work, our MusicXML) +
  prompt (interpretive space) + plaintext rights manifest. Zip container.
- **MusicXML is the existing roll.** The compressor adapts it; we are not in
  the business of scanning historic documents.
- **The deterministic player is the baseline** — "our MIDI player," free,
  proves the format. **The LLM player is the product** — the musician.
- **The seed workbench and LLM player are proprietary.** The open surface is
  the score side: encoding (S2), the deterministic player (P-series), the
  spec. Proprietary: seed authoring (C-series), LLM player (L-series). Spec +
  reference player go public at launch; split at pre-launch.
- **Tools before spec freeze.** The analyzer teaches us what the language
  needs; the diff tool teaches us whether compression works. Spec v1.0 is
  written from evidence, not ahead of it.
- **The corpus is the ratchet.** Bach → Byrd → Schubert → Beethoven 5 →
  Beethoven 9. Each rung gates the next; the Ninth is the v1.0 target.
- **No model training in the product path.** The LLM conductor is a stock,
  swappable model steered by prompt alone (seed + score + instructions).
  Delta analysis (score↔performance datasets) produces design knowledge —
  mockup schema fields, seed budgets, prompt vocabulary — never training
  data. Fine-tuning is an explicit escape hatch (plan B), not the plan.
  The intelligence migrates into the format, not the model.

## Phase 0 — Analysis workbench (tools that teach)

| Task | What it is | Status |
|---|---|---|
| W1 — Event-stream IR | Canonical in-memory event format all tools share: notes (pitch/onset/duration/velocity), tempo map, meter, key, dynamics, parts. Parsers: MusicXML in, MIDI in. | **done** (#123 + review follow-up #128 → [tools/ir](../tools/ir/)) |
| W2 — Corpus loader | Loads every [corpus/](../corpus/) file into the IR. Known-answer tests: note counts, part counts per source README. | **done (#125)** |
| W3 — Analyzer | Pattern detector over the IR: exact repeats, transposed repeats, sequences, mirror/retrograde candidates, ostinati. Outputs per-work statistics + pattern inventory. | **done #131** (tools/muse_analyze/, docs/analysis-report.md) |
| W4 — Diff tool | Event stream ↔ event stream: recall/precision in tick space. The ground truth for every compression claim. | **done #126** (tools/muse_diff/) |
| W5 — Visualizer | Piano-roll plots with pattern overlays. Human evaluation aid — the founder reviews what the analyzer claims. | **done #127** (tools/muse_viz/) |

**Phase 0 done when:** the analyzer has run across all five works and produced
a pattern-frequency report that drives Phase 1 language decisions.

## Phase 1 — Format spec v1.0 (from evidence)

| Task | What it is | Status |
|---|---|---|
| S1 — Event stream format | The decoder↔renderer contract: binary layout, tick resolution, dynamics curves. | **done** (#137 → [FORMAT_SPEC](../../FORMAT_SPEC.md) §4 + [tools/s1_stream](../tools/s1_stream/)) |
| S2 — Roll encoding | How the fixed score is packed: columnar, delta-encoded, entropy-coded. | **done (#138 → FORMAT_SPEC §4.6 + [tools/muse_roll](../tools/muse_roll/))** |
| S3 — Seed encoding | Interpretive parameters, sanctioned ranges, performance philosophy fields. | **decomposed #139 → S3.1–S3.6 (#142–#147); .1–.5 done, .6 open (#147)** |
| S4 — Language spec | The executable layer: operators (transpose/invert/retro/aug/dim), control flow, assertions. Informed by W3's pattern report. | **done (#140 → FORMAT_SPEC §5.1 + [tools/muse_ops](../tools/muse_ops/))** |
| S5 — Container + manifest | Zip layout, plaintext rights manifest, content hashes, signature. | **done (#141 → FORMAT_SPEC §7.1 + [tools/muse_mu](../tools/muse_mu/))** |

**Phase 1 done when:** FORMAT_SPEC.md v1.0 is written, with every construct
justified by Phase 0 evidence (a construct without corpus evidence doesn't ship).

## Phase 2 — Deterministic player (the baseline)

| Task | What it is | Status |
|---|---|---|
| P1 — Reference decoder | `.mu` roll stream → event stream. Deterministic, sandboxed, resource-bounded. | todo |
| P2 — Reference renderer | Event stream → audio (soundfont tier). CLI: `muse play file.mu`. | todo |
| P3 — Conformance suite | Golden vectors: (file → event stream) pairs. CI gate. | todo |

**Phase 2 done when:** every corpus `.mu` round-trips through the player and
the diff tool confirms the score reconstructs the source losslessly.

## Phase 3 — Seed authoring (the craft, proprietary)

| Task | What it is | Status |
|---|---|---|
| C1 — Seed format implementation | S3's spec → working reader/writer + validator. | **done (#148)** |
| C2 — AI-assisted authoring | LLM analyzes IR → proposes seed. Human reviews, edits, approves. | **done #153** (tools/muse_author/) |
| C3 — Expression-budget calibration | Delta-analysis-informed budget suggestions per era/style. | **done** (#175 → [tools/muse_budgets](../tools/muse_budgets/)) |
| C4 — Assertion authoring | Human writes constraints (must_contain, register, form) per work. | **done** (#182 → [tools/assertions](../tools/assertions/)) |

**Phase 3 done when:** seeds are authored for corpus works and validate
against S3 — the founder's ear gates quality. Design docs:
[design/](design/).

## Phase 4 — Mockup harness + renderer (the product)

| Task | What it is | Status |
|---|---|---|
| L1 — Mockup harness | score + seed → LLM → mockup at full DNA density. Generate → validate → fix, bounded retries. | **done #173** (tools/muse_mockup/) |
| L2 — Performance renderer | Mockup → audio via sfizz + SFZ samples (SSO/VPO tier). The "worth listening to" bar. | **done** (#193 → [tools/muse_render](../tools/muse_render/)) |
| L3 — Model comparison rig | Same score+seed, different LLMs → different mockups. Blind A/B listening. | todo |
| L4 — Distiller | Mockup → extracted interpretation → seed revision. The learning loop. | todo |

**Phase 4 done when:** one corpus work, performed by the LLM player, passes
the founder's by-ear evaluation as a musical performance — a reading worth a
hall.

## Phase 5 — The event (the unveiling)

| Task | What it is | Status |
|---|---|---|
| E1 — The work | One corpus work, fully seeded + mocked + rendered at concert quality. | todo |
| E2 — The venue | Concert hall, projection, the "giant computer" staging. | todo |
| E3 — The recording | Document the event; publish. | todo |

**Phase 5 done when:** deferred until Phase 4 produces one concert-worthy
work.

## Milestone barriers & decomposed sub-tasks

The scaffold-era risk list (blockers/ + session report) decomposed into
workable sub-tasks per TASK_WORKFLOW ("sub-tasks are decomposed from issues
that prove too large"). Each has a design-doc scaffold in
[design/](design/) and feeds the task it unblocks.

| Sub-task | Parent barrier | What it does | Unblocks |
|---|---|---|---|
| **W6 — B9 compute scaling** | Beethoven 9 (239k notes) through pattern analysis | Profiles W3's SIATEC pass; chooses suffix-array/SIATEC-C or sampling; pins per-tier compute budgets | W3 full-corpus pass |
| **W7 — Mockup schema v0** | L1's unwritten intermediate artifact | Drafts the mockup session-file schema from delta-analysis evidence + spike JSONs; validate via W4 | L1 harness |
| **C5 — Baroque delta measurement** | C3's unmeasured Baroque budget gap | Runs delta-analysis vocabulary on Baroque corpora (chorales + polyphony); feeds era budgets | C3 (and W3's per-phrase curves) |
| **L5 — Sample-quality waiver** | L2's unresolved "convincing vs. concert" ceiling | Triggered only if L2 fails the founder's ear despite maximal mockup: either commercial-library contract or revised event bar | E1 (event quality) |
| **S6 — Vocal text schema** | Vocal/choral text (Ninth 52 staves, FORMAT_SPEC §8) | Extends S1 with interleaved lyrics/syllables; verified against Beethoven 9 finale | S1 closure, v1.0 |
| **E4 — Extension decision** | `.mu` extension collision (Kerbal/Lisp) | Pick final file extension before spec publication (`.mu`, `.muse`, `.muw`, …); update spec + corpus + tooling | S5, publication |

Design docs: [design/w6-b9-scaling.md](design/w6-b9-scaling.md),
[design/w7-mockup-schema.md](design/w7-mockup-schema.md),
[design/c5-baroque-delta.md](design/c5-baroque-delta.md),
[design/l5-sample-waiver.md](design/l5-sample-waiver.md),
[design/s6-vocal-text.md](design/s6-vocal-text.md),
[design/e4-extension.md](design/e4-extension.md).

## Phase 2.5 — Integration (chained, gated, explorable)

| Task | What it is | Status |
|---|---|---|
| E2E chain harness | corpus source → IR → pack → container → decode → render, determinism-checked; the compose-proof for the landed parts. | **done** ([#162](https://github.com/allenpd728/muse/issues/162), tools/muse_chain/ + docs/chain-report.md) |
| CI conformance gate | W2/S1/S2/S5/chain gates run on every push; nothing guards merges today. | **done** ([#163](https://github.com/allenpd728/muse/issues/163), .github/workflows/) |
| Frontend explorer | QA-only static site: corpus browser + patterns + piano-rolls + pack stats (+audio when P2 lands). | **done** ([#164](https://github.com/allenpd728/muse/issues/164), docs/explorer/ + tools/muse_explorer/) |
| Integration testing scope | seam map + task breakdown; T1–T3 unblocked, T4–T5 wait on P1. | [docs/integration-testing-scope.md](integration-testing-scope.md) |
| T1 — Seam S2↔S5 | pack → container member → unpack round-trip, W4-diffed | **done** ([#165](https://github.com/allenpd728/muse/issues/165), tools/muse_roll/tests/) |
| T2 — S2 golden fixtures | pinned payload per corpus tier; drift fails byte-exact compare | **done** ([#166](https://github.com/allenpd728/muse/issues/166), tests/fixtures/) |
| T3 — Unified test runner | one command for all suites; fast/slow split; substrate for #163 | **done** ([#167](https://github.com/allenpd728/muse/issues/167), tools/run_tests.sh) |
| T4 — Seam S1→P1 | golden vectors feed P1 decoder when it lands | **done as stub contract** ([#168](https://github.com/allenpd728/muse/issues/168), DECODER swap pin); full verification awaits P1 |
| T5 — Chain test | full pipeline per corpus file via #162 + P1 | **done** ([#169](https://github.com/allenpd728/muse/issues/169), chain-report full registry) |
| Frontend QA tiers | T1 static contract (done #164); T2 headless DOM (Playwright); T3 live deploy smoke | T2 filed [#183](https://github.com/allenpd728/muse/issues/183), T3 filed [#184](https://github.com/allenpd728/muse/issues/184) |
| Seed workbench | explorer grown into the seed-iteration instrument panel: probes (W-B1), quality-check gate (W-B2), workbench page (W-B3), loop docs (W-B4) | [design](design/seed-workbench.md); W-B1 filed [#185](https://github.com/allenpd728/muse/issues/185), W-B2 [#186](https://github.com/allenpd728/muse/issues/186), W-B3 [#187](https://github.com/allenpd728/muse/issues/187), W-B4 [#188](https://github.com/allenpd728/muse/issues/188) |

## Explicitly not (yet)

- Public spec publication (pre-launch decision)
- Distribution/registry/marketplace
- Neural audio rendering (sample tier first)
- Notation-software and DAW plugins (post-launch)