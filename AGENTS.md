# AGENTS.md — Muse

Context and conventions for AI agents (and humans) working in this repository.

## What this project is

Muse is a **schema-first generative music platform**. A `.muse.json` file captures what makes a piece *this* piece (themes, motifs, form, harmony, constraints) and leaves open what a performer would decide (voicing, orchestration, microtiming, dynamics). Any capable model expands it into a performance; any conforming player renders it. The schema — not audio, not a prompt — is the canonical release artifact. See [`docs/vision.md`](docs/vision.md) for the full product thesis.

Components, in dependency order:

1. **Semantic schema** — spec lives in [`SCHEMA_SPEC.md`](SCHEMA_SPEC.md). Everything else conforms to it.
2. **Performance layer** — concrete expressive event format (spec gap; to be authored).
3. **Importer** — MIDI/MusicXML → `.muse.json` (not yet built).
4. **Interpreter** — any LLM expands schema + rendition into the performance layer (not yet built).
5. **Player** — V1 synthesis/samples, V2 optional audio-model plugins (not yet built).
6. **Composer interface** — node-based editor; deferred in favor of the importer.

## Ground rules

- **Schema-first.** Never bake musical decisions into the engine or UI that belong in the schema. If a behavior can't be expressed in the schema, extend the spec (with a version note), don't hard-code it.
- **The schema is a space, not a score.** Prefer ranges, constraints, and transforms over fixed values. A document that pins everything down is a bug, not thoroughness.
- **No artist lookalikes.** Rendition presets reference genres, eras, and production techniques only. Named-artist or voice-likeness targeting is prohibited unless an explicit license record is attached (see `metadata.license` in the spec).
- **Provenance is mandatory.** Any AI-generated or AI-assisted content added to a schema document must be recorded in `metadata.provenance`.
- **Engine-agnostic spec.** Spec changes must not privilege one rendering engine. Engine-specific knobs go in `extensions.<namespace>`.

## Conventions

- **Branching:** `main` is the stable branch. All day-to-day work happens on `dev` — agents and contributors branch from and merge into `dev` by default. `dev` merges into `main` via PR at meaningful milestones. Never commit directly to `main`.
- **Deploys:** the repo is linked to the Netlify site `muse-qa-58fd708e` as a **QA/design preview for the explorer only — never production**. Netlify is configured to build the `dev` branch only (dev branch deploy at `dev--muse-qa-58fd708e.netlify.app`), driven by `netlify.toml` (base `explorer/`). Rules: **never enable or trigger production builds** (no `main` builds, no "publish production deploy" action), **never add `netlify.toml` or a publishable build directory to `main`** outside the milestone-merge PR process, and **never change the site's branch/allow-list settings**. If a change to the deploy config seems needed, file a blocker instead — the free tier's build-minute budget is a human decision.
- **Task coordination:** Work is claimed and tracked per [`TASK_WORKFLOW.md`](TASK_WORKFLOW.md) — one task per GitHub issue, label-based states, commit directly to `dev`. Read it before picking up any task.
- **Blockers:** If you can't start or finish a task, don't guess — write `blockers/open_<datetime>_<slug>.md` per the protocol in `TASK_WORKFLOW.md` and move on to other work.
- **Tests:** Completing a task means also spec'ing its tests — `tests/open_<datetime>_<slug>.md` plus a linked `Tests:` issue, per the test-follow-up protocol in `TASK_WORKFLOW.md`. Code without a test spec is an incomplete task.
- **Schema documents:** JSON, validated against the spec; files use the `.muse.json` extension (once examples/tooling land).
- **Spec edits:** keep the changelog discipline — `muse_version` is semver; v0.x may break, v1+ additive only.
- **Code style:** minimal comments; comment only non-obvious invariants or deliberate tradeoffs. Keep changes focused and small.
- **Docs:** `PRIOR_ART_REVIEW.md` is the landscape review that motivated design decisions — read it before proposing pivots.

## Build / test

Nothing to build yet — the repo currently contains documents only. When tooling lands:

- Schema validation: JSON Schema validator against example documents in `examples/` (planned).
- Engine conformance: motif-recall and structure-fidelity harness (planned).

Update this section as tooling is added; do not leave it stale.

## Repository layout (planned)

```
SCHEMA_SPEC.md        # normative spec (this is the source of truth)
PRIOR_ART_REVIEW.md   # landscape research
TASK_WORKFLOW.md      # multi-agent task claiming/blocker protocol
README.md             # vision + architecture
docs/                 # vision, milestone scope docs
blockers/             # open_/closed_ blocker reports needing human input
tests/                # open_/closed_ test specs written per completed task
examples/             # example .muse.json documents (planned)
schema/               # JSON Schema validation files (planned)
tools/                # validator CLI + test harness (planned)
importer/             # MIDI/MusicXML → .muse.json (planned)
interpreter/          # LLM prompt + expansion logic → performance layer (planned)
player/               # performance renderer (planned)
composer/             # node-based authoring UI (deferred)
```
