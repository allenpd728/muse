# Muse Format Specification — v0 (Design Draft)

**Status:** Design draft, pre-evidence. The language and encoding details are
pinned by Phase 0/1 work (see [docs/pipeline.md](docs/pipeline.md)); this
document defines the model they must serve. Nothing here is implemented.

## 0. The one-sentence definition

**A `.mu` file is the compressed, executable encoding of a musical work — two
streams in one container.** The **roll stream** is the fixed score: what
MusicXML already carries, compressed and packaged (our MusicXML). The **seed
stream** is the interpretive space: what may vary, and the performance
philosophy that guides the variation. A deterministic player reads the roll;
an LLM player reads roll + seed and brings the work to life.

The metaphor: the `.mu` file is the improved piano roll — re-punched with
modern musical knowledge so the existing player piano produces a better
performance. Technology advancing hardware by changing the software.

## 1. The two streams

| | **Roll stream** | **Seed stream** |
|---|---|---|
| What it is | The fixed score | The interpretive space |
| Contents | Notes, structure, form, dynamics | Sanctioned ranges, performance philosophy, variation points |
| Read by | Deterministic player (baseline) | LLM player (product) |
| Playback | Identical everywhere, forever | Interpreted; varies by performer within sanctions |
| Analogy | Our MIDI / the punched roll | The conductor's margin notes |

The roll stream answers "what is the work." The seed stream answers "how may
it live." The roll constrains the seed; the seed never contradicts the roll.

## 2. Design goals

1. **Compression by construction.** The roll stream is MusicXML compressed:
   columnar, delta-encoded, pattern-factored, entropy-coded. Program length
   versus expanded output is a measurable property of the work.
2. **Determinism at the baseline.** Same `.mu` → identical roll playback on
   every conforming player, forever. Conformance is byte-exact.
3. **Interpretation as data.** The seed stream is explicit, inspectable, and
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

## 4. The roll stream (encoding sketch)

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

## 5. The seed stream (model)

The seed stream declares the **sanctioned space** — what a performance may
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

**Advocacy rule.** The composer (or encoder) is the work's advocate; the seed
stream is the advocacy instrument. Wildly different readings are valid when
they satisfy the assertions — the Gould/Bernstein case is in-spec. What is
out-of-spec is violating the roll: the assertions fail and playback refuses.

## 6. Execution model

```
roll.bin  ──decode──▶ event stream ──▶ renderer ──▶ audio   (deterministic path)

roll.bin + seed.bin + interpretation request ──▶ LLM expansion
    ──▶ expressive event stream ──▶ validate against assertions
    ──▶ renderer ──▶ audio                                          (product path)
```

- **Deterministic path**: decode → render. No AI, no network, no ambiguity.
  This is the free baseline and the conformance target.
- **Product path**: the LLM player interprets within the seed space, bounded
  by the roll. Generate → validate → fix, bounded retries, fail loudly.
  Provenance (model, timestamp) is stamped by the harness, never trusted to
  the model.
- **Renderer tiers**: soundfont (baseline) → samples (the "worth listening
  to" bar) → neural (later). The event stream is the contract; renderers
  compete below it.

## 7. Conformance and versioning

- **Decoder conformance**: golden vectors — `.mu` → event stream, byte-exact,
  including resource-bound behavior. A decoder conforms or it doesn't.
- **Work conformance**: every corpus work round-trips — source → `.mu` →
  event stream, diff green. The corpus ladder gates versions; the complete
  Beethoven 9 is the v1.0 target.
- **`format_version` is semver.** v0.x may break; v1+ additive only.

## 8. Open questions (to be pinned by Phase 0/1)

- Exact roll packing scheme (driven by analyzer statistics).
- Seed-stream field set (driven by compression experiments).
- Whether the executable layer needs a general operator set (transpose/
  invert/retro/aug/dim) or the corpus demands more.
- Performance-file encoding details.
- How vocal/choral text is carried (the Ninth's finale forces this).
