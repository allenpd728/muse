# Muse Format Specification — v0 (Design Draft)

**Status:** Design draft, pre-evidence. The language and encoding details are
pinned by Phase 0/1 work (see [docs/pipeline.md](docs/pipeline.md)); this
document defines the model they must serve. Nothing here is implemented.

## 0. The one-sentence definition

**A `.mu` file is the compressed, executable encoding of a musical work —
three components in one container.** The **score** is the fixed work: what
MusicXML already carries, packaged (our MusicXML). The **prompt** is the
interpretive space: what may vary, and the performance philosophy that guides
the variation. The **manifest** carries rights and provenance in plaintext. A
deterministic player reads the score; an LLM player reads score + prompt and
brings the work to life — slowly, deliberately. A performance is an event,
not a render.

The metaphor: the `.mu` file is the improved piano roll — re-punched with
modern musical knowledge so the existing player piano produces a better
performance. Technology advancing hardware by changing the software.

## 1. The three components

| | **Score** | **Prompt** | **Manifest** |
|---|---|---|---|
| What it is | The fixed work | The interpretive space | Rights + provenance |
| Contents | Notes, structure, form, dynamics | Sanctioned ranges, performance philosophy, variation points | License, authorship, AI disclosure, hashes |
| Read by | Deterministic player (baseline) | LLM player (product) | Anyone — plaintext |
| Playback | Identical everywhere, forever | Interpreted; varies by performer within sanctions | — |
| Analogy | Our MIDI / the soil | The seed / the water | The label |

The score answers "what is the work." The prompt answers "how may
it live." The score constrains the prompt; the prompt never contradicts the score.

## 2. Design goals

1. **Compression by construction.** The score is MusicXML compressed:
   columnar, delta-encoded, pattern-factored, entropy-coded. Program length
   versus expanded output is a measurable property of the work.
2. **Determinism at the baseline.** Same `.mu` → identical score playback on
   every conforming player, forever. Conformance is byte-exact.
3. **Interpretation as data.** The prompt is explicit, inspectable, and
   licensed — interpretive decisions are first-class, declared, and bounded.
4. **Rights travel in plaintext.** The manifest is human-readable without
   tooling or execution: license, provenance, AI disclosure.
5. **The decoder is dumb.** All intelligence lives at compression time
   (offline, AI-assisted) or in the LLM player (the product). Baseline
   decoding is pure evaluation.
6. **Evidence-driven design.** Every language construct and encoding choice
   must be justified by corpus analysis (Phase 0). No speculative features.

## 3. File anatomy

A `.mu` file is a zip container (the `.mxl` precedent):

```
work.mu
├── manifest.json      ← REQUIRED. Plaintext. Rights + provenance + hashes.
├── roll.bin           ← REQUIRED. The fixed score, compressed.
├── seed.bin           ← REQUIRED. The interpretive space.
└── performances/      ← OPTIONAL. Certified expansions (see §6).
    └── *.perf
```

**`manifest.json`** — the only human-readable member, by design:
`format_version`, work id, title, composer, license (`renditions:
presets-only | open-within-constraints | closed`, attribution, commercial),
provenance (source, tools, AI involvement disclosure), content hashes of all
other members, signature.

**`roll.bin`** — the compressed score. Encoding pinned by tasks S1–S2:
event-stream format, packing scheme, entropy coding. Baseline: lossless
against the source MusicXML event stream, verified by the diff tool (W4).

**`seed.bin`** — the interpretive space. Encoding pinned by task S3:
sanctioned parameter ranges, performance-philosophy declarations, variation
points with bounds. Human-authored or human-approved at compression time —
the conductor layer. Never machine-invented without review.

**`performances/*.perf`** — cached, certified expansions (composer-approved
renders), each recording the seed settings and content hash it was produced
from. Cached computation, never the definition of the work. Zero-compute
first listen.

## 4. The score (encoding sketch)

Baseline content model — what MusicXML carries that we preserve:

- **Parts** with instrument identity (name, GM program where applicable).
- **Notes**: pitch, onset, duration, velocity — integer ticks (PPQ) and fixed
  point; no float nondeterminism.
- **Maps**: tempo, meter, key — full maps, not flattened opening values
  (mid-piece changes are preserved, unlike the old importer).
- **Expression**: dynamics markings and hairpins, articulations, fermatas,
  repeats and endings — the notated performance layer.
- **Structure**: measures, sections, repeat topology.

Packing: columnar arrays, delta-encoded onsets, dictionary-coded repeated
patterns, entropy-coded residual. The pattern-factoring layer (sequences,
transposed repeats, imitative entries) is driven by analyzer evidence (W3).

## 5. The prompt (model)

The prompt declares the **sanctioned space** — what a performance may
vary — plus the **philosophy** that guides it:

- **Parameters with ranges**: tempo bounds, variation level, density, energy.
  A performance chooses points inside; it can never reach outside.
- **Philosophy declarations**: tempo philosophy ("flexible, architectural"),
  dynamic philosophy ("terraced, dramatic"), articulation stance. Free-text +
  typed fields; references styles and practices, never artist identities
  without a license record.
- **Variation points**: where the work permits interpretation (ornamentation
  zones, optional repeats, cadenza-like freedoms), each with bounds.
- **Assertions**: invariants every performance must satisfy (theme recall,
  register bounds, structural form). The LLM player's output is validated
  against these; failure is loud, never silent deviation.

**Advocacy rule.** The composer (or encoder) is the work's advocate; the prompt
is the advocacy instrument. Wildly different readings are valid when
they satisfy the assertions — the Gould/Bernstein case is in-spec. What is
out-of-spec is violating the score: the assertions fail and playback refuses.

## 6. Execution model

```
BASELINE PATH (deterministic):
score ──decode──▶ event stream ──▶ renderer ──▶ audio

PRODUCT PATH (the musician):
score + prompt ──▶ LLM session work ──▶ mockup ──▶ validate vs. assertions
    ──▶ renderer ──▶ audio

LEARNING LOOP:
mockup ──distill──▶ improved prompt (new seed) ──▶ next mockup is better
```

- **The mockup is the intermediate artifact.** The LLM does not "perform" — it
  does session work: tempo map, dynamic curves, velocities, articulation,
  balance. The mockup is the session file (expressive-MIDI-class data:
  onset/duration/velocity/articulation + tempo map + curves + per-part
  balance). The renderer turns the mockup into audio via sample playback
  (sfizz/SFZ tier) — existing open technology, not built here.
- **Deterministic path**: decode → render. No AI, no network, no ambiguity.
  The free baseline and the conformance target.
- **Product path**: the LLM interprets within the prompt space, bounded by
  the score. Generate → validate → fix, bounded retries, fail loudly.
  Provenance (model, timestamp) is stamped by the harness, never trusted to
  the model. Deliberation takes time — a performance is an event.
- **The learning loop**: mockups are distilled back into prompts (new seeds).
  The prompt accumulates interpretive craft; later mockups are cheaper and
  better. Every prompt revision records which mockups informed it.
- **Machine-readable except the manifest.** Score, prompt, and mockup are
  data for machines. Human readability lives in tooling (decode/trace), not
  in the formats. The manifest stays plaintext — rights are for lawyers.
- **Renderer tiers**: soundfont (baseline) → SFZ/samples via sfizz (the
  "worth listening to" bar — no DAW engineering required) → neural (later).
  The event stream / mockup contract is the seam; renderers compete below it.

## 6.1 Source-agnostic seed authoring

The prompt is authored from **any source**, via the IR (the canonical
event-stream representation every tool shares):

| Source | What the author sees | Prompt richness |
|---|---|---|
| MusicXML | Notation semantics: dynamics, articulation, form | Richest — everything explicit |
| DAW session | A producer's mockup: tempo map, curves, balance | Interpretation partially present — the prompt can learn from a human session |
| MIDI | Pitch × time only (the two-dimensional tree) | Sparse — structure inferred, inferences marked |

Richer sources author richer prompts; poorer sources author sparser prompts
with marked inferences (recorded in the manifest). The prompt is never
finished — it is re-authored and revised as tools improve.

## 7. Conformance and versioning

- **Decoder conformance**: golden vectors — `.mu` → event stream, byte-exact,
  including resource-bound behavior. A decoder conforms or it doesn't.
- **Work conformance**: every corpus work round-trips — source → `.mu` →
  event stream, diff green. The corpus ladder gates versions; the complete
  Beethoven 9 is the v1.0 target.
- **`format_version` is semver.** v0.x may break; v1+ additive only.

## 8. Open questions (to be pinned by Phase 0/1)

- Exact score packing scheme (driven by analyzer statistics).
- Prompt field set (driven by compression experiments).
- Whether the executable layer needs a general operator set (transpose/
  invert/retro/aug/dim) or the corpus demands more.
- Performance-file encoding details.
- How vocal/choral text is carried (the Ninth's finale forces this).
