# Muse

**An executable music format.** A `.muse` file is a small, deterministic
program: executed by any conforming player with a set of rendition parameters
and a seed, it computes a complete musical performance. The file is not a
recording, not a score, not a description of notes — it is the compressed
procedure that produces them.

Think L-systems for music: themes, variations, and form as a generator. The
same file yields different valid performances under different rendition
parameters — the work persists; interpreters differ.

> **Status: pivot / design phase.** The repo is documents-only. The earlier
> JSON-schema pipeline (validator, importer, interpreter, player, explorer)
> was removed and is recoverable from git history. The design now lives in
> [`FORMAT_SPEC.md`](FORMAT_SPEC.md); the build order lives in
> [`docs/pivot-tasks.md`](docs/pivot-tasks.md).

## The three components

| Component | What it is | Status |
|---|---|---|
| **Format spec** | The language, deterministic execution model, container, and conformance definition — the product itself | Draft: [`FORMAT_SPEC.md`](FORMAT_SPEC.md) |
| **Compressor** | AI analyzes MIDI/MusicXML and writes the shortest program that expands back to the work (compress → expand → diff → adjust). Also the direct-authoring path for new works | Task T5 |
| **Player** | Reference decoder (program + params + seed → event stream), swappable renderers (event stream → audio), and the UI for picking renditions and steering parameters | Tasks T2–T4, T6 |

## Why a program, not a prompt, not a schema

- **Structure is enforceable.** Constraints are assertions in the code,
  checked against the program's own output at execution time.
- **Compression is the feature.** Program length versus expanded output is a
  measurable property of the work — the format's quality metric falls out of
  its encoding.
- **Provenance and rights.** The container carries a plaintext manifest:
  license, authorship, AI-involvement disclosure. Readable without executing
  anything.
- **Determinism.** Same program + params + seed → identical performance, on
  every conforming player, forever. That is what makes conformance testable
  and players interchangeable.

## Principles

1. **Format-first.** The spec is the product. Everything else is a client of it.
2. **Composer-owned.** Composers retain authorship and control over works and sanctioned renditions.
3. **Genre covers, not artist lookalikes.** Renditions reference styles, eras, and production treatments — never the voice or likeness of an artist without an explicit opt-in license.
4. **Open by default.** The spec is published openly; any conforming player renders any conforming file.
5. **Standalone.** Muse is its own playback surface; distribution to existing services is optional and downstream.
