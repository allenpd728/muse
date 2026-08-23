# AGENTS.md — Muse

Context and conventions for AI agents (and humans) working in this repository.

## What this project is

Muse is an **executable music format**. A `.muse` file is a small,
deterministic program: executed by a conforming player with rendition
parameters and a seed, it computes a complete musical performance. The format
spec — not audio, not a prompt, not a schema — is the product. See
[`FORMAT_SPEC.md`](FORMAT_SPEC.md) for the design and [`docs/vision.md`](docs/vision.md)
for the product thesis.

> **Pivot state: documents-only.** The earlier JSON-schema pipeline (validator,
> importer, interpreter, player, explorer, benchmark) was removed in the pivot
> and is recoverable from git history (`git log` prior to the
> `pivot/executable-format` branch). [`SCHEMA_SPEC.md`](SCHEMA_SPEC.md) is kept
> as design history only — it is superseded, not normative.

Components (build order per [`docs/pivot-tasks.md`](docs/pivot-tasks.md)):

1. **Format spec** — the language, execution model, container, conformance.
2. **Reference decoder** — program + params + seed → event stream (T2).
3. **Renderer** — event stream → audio, swappable tiers (T4).
4. **AI compressor** — MIDI/MusicXML → program via compress → expand → diff (T5).
5. **Player UI** — rendition/parameter steering (T6).

## Ground rules

- **Format-first.** Never bake musical decisions into a decoder, renderer, or
  UI that belong in the language. If a behavior can't be expressed in the
  format, extend the spec (with a version note), don't hard-code it.
- **Determinism is sacred.** Same program + params + seed → identical output
  everywhere, forever. Any feature that threatens this (wall-clock, ambient
  state, platform-dependent float behavior) is rejected at spec review.
- **The decoder stays dumb.** Intelligence belongs in the compressor
  (authoring) or in swappable renderer plugins — never required for decoding.
- **No artist lookalikes.** Renditions reference styles, eras, and production
  techniques only. Named-artist or voice-likeness targeting requires an
  explicit license record in the manifest.
- **Provenance is mandatory.** AI-generated or AI-assisted content is recorded
  in the manifest's provenance — including compressor output.
- **Spec before code.** No implementation task starts before its spec section
  is stable enough to write acceptance criteria against.

## Conventions

- **Branching:** `main` is stable; day-to-day work branches from and merges
  into `dev`. Never commit directly to `main`.
- **Task coordination:** one task per GitHub issue, label-based states, per
  [`TASK_WORKFLOW.md`](TASK_WORKFLOW.md). Current task list:
  [`docs/pivot-tasks.md`](docs/pivot-tasks.md).
- **Blockers:** can't start or finish? Write
  `blockers/open_<datetime>_<slug>.md` per TASK_WORKFLOW.md and move on.
- **Tests:** completing a task means spec'ing its tests
  (`tests/open_<datetime>_<slug>.md` + linked `Tests:` issue).
- **Spec edits:** changelog discipline — `format_version` is semver; v0.x may
  break, v1+ additive only.
- **Docs:** `PRIOR_ART_REVIEW.md` covers the old schema-first landscape; the
  executable-format prior-art appendix is task P1. Read both before proposing
  pivots.

## Build / test

Nothing to build — the repo currently contains documents only. CI returns with
the first code task (T2). Update this section as tooling lands; do not leave
it stale.

## Repository layout

```
FORMAT_SPEC.md        # the executable-format spec (design draft — source of truth)
README.md             # pivot overview + component map
SCHEMA_SPEC.md        # SUPERSEDED (JSON-schema v0) — design history only
PRIOR_ART_REVIEW.md   # landscape research (schema-first era)
TASK_WORKFLOW.md      # multi-agent task claiming/blocker protocol
docs/vision.md        # product thesis
docs/pivot-tasks.md   # build order + task list (T0–T6, P1)
blockers/             # open_/closed_ blocker reports
tests/                # open_/closed_ test specs (process history; no suites yet)
```
