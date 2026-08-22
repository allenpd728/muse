# Muse

**Schema-first generative music.** Composers author portable, machine-readable composition blueprints; a generative audio engine renders them into finished music in real time; listeners experience each composition through multiple sanctioned renditions — different genres, styles, and production treatments of the same underlying work.

Think of a film-score composer delivering the thematic skeleton of a film, with orchestrators and producers turning it into the final soundtrack. Muse turns that division of labor into a platform: the composer's schema is the canonical release artifact, and each rendition is a first-class, licensed derivative of it.

## Architecture

Muse is built as four layers:

| Layer | What it is | Status |
|---|---|---|
| **Semantic schema** | JSON-native specification describing a composition as a *space of valid renditions*: tempo, meter, form, sections, themes, motifs, variations, rhythms, harmony, constraints, and rendition hooks | [Draft spec](SCHEMA_SPEC.md) |
| **Composer interface** | Node-based visual authoring environment (DAW/Sibelius-class UX) that compiles to the schema | Not started |
| **Generative audio engine** | AI that interprets a schema + rendition parameters in real time and renders audio, enforcing long-range structure (motif recall, theme development, form) | Not started |
| **Listener front end** | Listening platform where users select composers and switch between renditions ("genre covers") of the same schema | Not started |

## Why a schema, not a prompt

- **Structure is enforceable.** Text-to-music systems (Suno, Udio, MusicGen) notoriously fail at long-range structure — recurring themes, motivic development, intentional form. A schema gives the engine the scaffolding those systems lack.
- **Provenance and rights.** A human-authored schema is a copyrightable musical work. Renditions are traceable derivatives of it, which aligns with the post-2025 industry's move toward licensed, opt-in, auditable generation.
- **Portability.** The schema is an open, inspectable document — not a proprietary session file or a hidden model state. Composers own it; engines compete to render it.

## Interpreter providers

`tools/play.mjs` and `interpreter/expand.mjs` share the same provider order — **offline → Gemini free tier → paid adapters**:

- **Offline** (default): deterministic rule-based expander, no API key.
- **`MUSE_PROVIDER=gemini`** + `GEMINI_API_KEY`: Google AI Studio free tier; requests structured JSON (`responseMimeType: application/json`). Default model: `gemini-2.0-flash`.
- **`MUSE_PROVIDER=anthropic`** + `ANTHROPIC_API_KEY`, or **`MUSE_PROVIDER=openai`** + `OPENAI_API_KEY`: paid adapters.

All live-model paths feed the generate → validate → fix loop; a performance that can't satisfy the constraints after bounded retries fails loudly.

## Repository contents

- [`SCHEMA_SPEC.md`](SCHEMA_SPEC.md) — Muse Schema Specification v0 (draft)
- [`PRIOR_ART_REVIEW.md`](PRIOR_ART_REVIEW.md) — landscape and prior-art review informing the design
- [`AGENTS.md`](AGENTS.md) — project conventions and context for AI coding agents

## Principles

1. **Schema-first.** The schema is the product. Everything else renders from it.
2. **Composer-owned.** Composers retain authorship and control over schemas and sanctioned renditions.
3. **Genre covers, not artist lookalikes.** Rendition presets reference styles, eras, and production treatments — never the voice or likeness of an artist without an explicit opt-in license.
4. **Open by default.** The schema spec is published openly; interoperability (MusicXML/MIDI import) is a feature, not a threat.
5. **Standalone.** Muse is its own playback surface; distribution to existing streaming services is optional and downstream.
