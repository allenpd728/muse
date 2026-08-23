# Muse Format Specification — v0 (Design Draft)

**Status:** Design draft. Nothing here is implemented. This document supersedes
the JSON-schema lineage ([SCHEMA_SPEC.md](SCHEMA_SPEC.md), kept as design
history). It defines what a `.muse` file *is* before any code exists.

## 0. The one-sentence definition

**A `.muse` file is a program.** Writing one means authoring a generator: a
small, deterministic program that — executed by a conforming player with a set
of rendition parameters and a seed — evaluates to a complete musical
performance. The file is not a recording, not a score, not a description of
notes. It is the compressed *procedure* that produces them.

This is the L-system insight applied to music: a short axiom plus rewriting
rules yields a complex structure. Beethoven's Ninth is highly compressible
because it is themes, variations, and recursion. A Muse file encodes exactly
that compressibility. The compression ratio of a work — program length versus
expanded output — is a measurable property of the music itself.

## 1. Design goals

1. **Executable, not declarative.** The file does not describe a performance
   space; it *computes* one. Motifs, themes, form, and variations are program
   structure, not data fields.
2. **Deterministic by construction.** Same program + same rendition parameters
   + same seed → byte-identical event stream, on every conforming player,
   forever. This is the property that makes conformance testable.
3. **Sandboxed.** A program can compute music and nothing else: no I/O, no
   clock, no network, no unbounded resources.
4. **Renditions as inputs, not files.** A rendition is a parameter bundle
   passed to the program at execution time. The composer declares which
   parameters exist and their sanctioned ranges; the listener chooses values
   inside them.
5. **Rights travel in plaintext.** The container carries a human-readable
   manifest (license, provenance, attribution) that requires no execution and
   no tooling to read. Everything else may be opaque.
6. **The decoder is dumb.** All intelligence lives in authoring (the AI
   compressor) or in optional expression stages. Decoding is pure evaluation
   any conforming implementation can perform cheaply.

## 2. What writing a `.muse` file means

The author's job is to find the *generative essence* of the work and express
it in the language:

- **Themes and motifs** are named phrases — values in the program.
- **Variation** is operator application: transpose, invert, retrograde,
  augment, diminish, reharmonize, re-voice.
- **Form** is control flow: sections, repeats, development as parameter-driven
  branching.
- **Constraints** are assertions in the code — checked against the program's
  own output at execution time, so a non-conforming performance fails loudly
  instead of shipping silently.
- **Interpretive freedom** is explicit: parameters with declared ranges. What
  the composer leaves open, the rendition decides. What the composer pins, no
  rendition can move.

Two authoring paths exist, both producing the same artifact:

- **AI compression** — the compressor analyzes an existing MIDI/MusicXML work
  and searches for a short program that expands to it (compress → expand →
  diff → adjust, iterated against a corpus).
- **Direct authoring** — a composer (or an agent acting for one) writes the
  program from scratch. No DAW, no intermediate notation.

## 3. File anatomy

A `.muse` file is a zip container (the `.mxl` precedent):

```
night-circuit.muse            (zip)
├── manifest.json             ← REQUIRED. Plaintext. Rights + provenance.
├── program.mu                ← REQUIRED. The work, in canonical source form.
└── performances/             ← OPTIONAL. Pre-baked, certified executions.
    ├── r.original.perf
    └── r.quartet.perf
```

**`manifest.json`** — the only human-readable member, by design. Contains:
`format_version`, work id, title, composer, license (`renditions:
presets-only | open-within-constraints | closed`, attribution, commercial),
provenance (including mandatory AI-involvement disclosure), and content
hashes of every other member. A lawyer reads this with a text editor.

**`program.mu`** — the work. UTF-8 canonical source. (A bytecode serialization
is a possible future optimization; it must be semantics-preserving and is an
open question, §9 — not v0.)

**`performances/*.perf`** — cached executions of this program under specific
parameter bundles, recorded with the parameter values, seed, and the content
hash of the `program.mu` they were produced from. Baked performances let a
listener hear the composer's certified versions with zero computation; stale
ones are detectable by hash mismatch. They are cached computation, never the
definition of the work.

## 4. The language (illustrative core)

Syntax below is **illustrative, not normative** — it exists to make the model
concrete. Pinning the grammar is task T1 (see `docs/pivot-tasks.md`).

```lisp
work "Ode Fragment" {
  // Rendition-controllable inputs, with sanctioned ranges and defaults.
  params {
    tempo_bpm:  60..120  default 96
    variation:  0..2     default 0
  }

  // A named phrase: pitch+duration pairs. Durations in note values (q, e, h).
  theme ode = phrase(
    (E4 q) (E4 q) (F4 q) (G4 q)
    (G4 q) (F4 q) (E4 q) (D4 q)
    (C4 q) (C4 q) (D4 q) (E4 q)
    (E4 q.) (D4 e) (D4 h)
  )

  section main {
    voice celli  { play ode, pp }
    voice violin { play ode @ transpose(+12), mf, when variation >= 1 }
  }

  // Constraints are code. Checked against the program's own output.
  assert contains(ode)
  assert register(celli, C2..C4)
}
```

Core primitives the language must provide:

- **Events**: pitched notes (12-TET v0), rests, durations in note values and
  ticks. Voices/parts as first-class executors.
- **Transforms**: `transpose`, `invert`, `retro`, `augment`, `diminish` —
  composable operators over phrases (the old schema's transform-ref grammar,
  promoted from data to code).
- **Structure**: sections, repeats with bounded ranges, parameter-conditional
  execution (`when`).
- **Expression**: dynamics markings with deterministic rendition-level mapping
  to velocity/timing curves (expression maps are declared in the work and may
  be overridden within sanctioned ranges by the rendition).
- **Randomness**: explicit `seed` input only; a seeded PRNG is the single
  source of nondeterminism and is fully reproducible.
- **Assertions**: `contains`, `register`, tempo bounds, structural invariants.
  Evaluated against the emitted event stream; failure aborts execution loudly.

## 5. Execution model

```
program.mu + rendition params + seed  ──▶  event stream  ──▶  renderer ──▶ audio
              (deterministic VM)         (decoder output)     (swappable)
```

The decoder's output — the **event stream** — is the contract between the
format and all renderers. It is the surviving idea from the old performance
layer: absolute ticks (integer PPQ), per-part note events with pitch, onset,
duration, velocity, articulation; a tempo map; optional per-note controllers.
Renderers (GM tier, sample tier, neural tier) consume only this stream. The
stream format is versioned with the format spec.

The **trace** — which phrase instances and transforms produced which spans of
the output — is available in a debug execution mode. This is what the old
"crosswalk" design was groping toward: alignment is not stored data, it is
the program's own execution record.

## 6. Determinism and sandboxing (normative)

A conforming decoder:

1. Produces byte-identical event streams for identical (program, params, seed).
2. Uses integer ticks and fixed-point arithmetic only — no floating-point
   nondeterminism across platforms.
3. Provides no I/O, no wall-clock, no environment access.
4. Enforces resource bounds: a step limit and memory cap. Every valid program
   must terminate; an unterminated execution is a decoder-visible error, not a
   hang.
5. Treats unknown-but-valid language features from newer minor versions per
   the versioning rules (§8).

## 7. Renditions

A rendition is a named parameter bundle plus provenance — the successor of the
old schema's `renditions[]`. Parameters may only be chosen within the ranges
the work declares. Listener interaction (steering energy, density, variation
level, tempo within range) *is* parameter selection; it can never reach
outside the sanctioned space, which is what keeps provenance and licensing
meaningful. Renditions are themselves creditable, licensable works.

## 8. Conformance and versioning

Two conformance levels:

- **Decoder conformance** — the conformance suite is a set of (program,
  params, seed) → golden event stream vectors. A decoder conforms if it
  reproduces every vector byte-exactly, including resource-bound and
  assertion-failure behavior.
- **Work conformance** — a work conforms if its assertions hold for every
  sanctioned parameter combination exercised by the suite.

`format_version` is semver. v0.x may break freely; v1+ is additive only.

## 9. Open questions

- **Voices and lyrics.** The Ninth's finale forces this: text, syllable-note
  alignment, vocal timbre parameters. Also the unlock for the entire song
  market. Highest-priority open design problem.
- **Bytecode serialization** of `program.mu` (size/speed vs. toolchain cost).
- **Microtonality** beyond 12-TET.
- **Expression-map formality** — how much of interpretation (rubato, phrasing)
  is program, how much is rendition, how much is renderer.
- **Program-size vs. baked-perf tradeoffs** for very large works.
