# AGENTS.md — Muse

Context and conventions for AI agents (and humans) working in this repository.

## What this project is

Muse is a **schema-first generative music platform**. Composers author a semantic schema describing a composition (tempo, meter, form, sections, themes, motifs, variations, rhythms, harmony, constraints); a generative audio engine renders the schema in real time; listeners choose among sanctioned **renditions** (genre/style treatments) of the same work. The schema — not audio, not a prompt — is the canonical release artifact.

Four layers, in dependency order:

1. **Semantic schema** — spec lives in [`SCHEMA_SPEC.md`](SCHEMA_SPEC.md). Everything else conforms to it.
2. **Composer interface** — node-based visual editor that compiles to the schema (not yet built).
3. **Generative audio engine** — renders schema + rendition params to audio (not yet built).
4. **Listener front end** — rendition selection and playback (not yet built).

## Ground rules

- **Schema-first.** Never bake musical decisions into the engine or UI that belong in the schema. If a behavior can't be expressed in the schema, extend the spec (with a version note), don't hard-code it.
- **The schema is a space, not a score.** Prefer ranges, constraints, and transforms over fixed values. A document that pins everything down is a bug, not thoroughness.
- **No artist lookalikes.** Rendition presets reference genres, eras, and production techniques only. Named-artist or voice-likeness targeting is prohibited unless an explicit license record is attached (see `metadata.license` in the spec).
- **Provenance is mandatory.** Any AI-generated or AI-assisted content added to a schema document must be recorded in `metadata.provenance`.
- **Engine-agnostic spec.** Spec changes must not privilege one rendering engine. Engine-specific knobs go in `extensions.<namespace>`.

## Conventions

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
README.md             # vision + architecture
examples/             # example .muse.json documents (planned)
schema/               # JSON Schema validation files (planned)
composer/             # node-based authoring UI (planned)
engine/               # generative rendering engine (planned)
listener/             # listener-facing app (planned)
```
