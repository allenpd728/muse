# Pivot tasks — executable format build order

The repo is documents-only. This is the build order for the executable-format
design defined in [FORMAT_SPEC.md](../FORMAT_SPEC.md). House rules per
[TASK_WORKFLOW.md](../TASK_WORKFLOW.md): one task per GitHub issue, label
states, commit to `dev`.

## Decisions (locked)

- **Spec before code.** No implementation task starts before its spec section
  is stable enough to write acceptance criteria against. Code written ahead of
  the spec is deleted, not iterated (see: the JSON pipeline).
- **Build order: spec → decoder → renderer → compressor → UI.** The decoder
  defines what "expand" means; the compressor's diff loop is meaningless until
  the expansion target exists. The compressor is built *last* of the core
  components even though it is the AI showcase.
- **The decoder is the product's center of gravity.** It is small, total,
  deterministic, dependency-free, and conformance-tested. Everything else is a
  client of it.
- **Docs-only until T2 lands.** No package.json, no CI, no fixtures until
  there is code that justifies them. Test assets (MIDI/MusicXML corpus) return
  with the tasks that consume them, not before.
- **The Ninth is the v1.0 conformance target.** Every component's done-criteria
  ladder ends at "carries Beethoven's Ninth" (chorale → sonata → Ninth).

## Task list

### T0 — Format spec review gate (this + FORMAT_SPEC.md)
Done when: the spec's open questions (§9) are either resolved or explicitly
deferred, and the illustrative language sketch (§4) is agreed as the design
direction. No code exists before this gate.

### T1 — Language spec v0
Pin the grammar, execution semantics, determinism rules, and event-stream
format from FORMAT_SPEC.md §4–6. Includes hand-authoring three example
programs: an Ode-to-Joy fragment, a Bach chorale phrase, one generative pop
sketch (to prove the language serves both faithful and generative modes).
Done when: the spec is complete enough that two people could independently
write the same program for a given phrase and agree on the expected output.

### T2 — Reference decoder
Dependency-free implementation: `program.mu` + params + seed → event stream,
with the trace (debug) mode and assertion checking. Plus the first conformance
vectors (T1's example programs with golden outputs).
Done when: conformance vectors pass byte-exactly; fuzzed invalid programs fail
loudly within resource bounds, never hang.

### T3 — Conformance suite + corpus ladder
The (program, params, seed) → golden-stream suite, and acquisition of the
public-domain corpus: Bach chorales → Mozart/Beethoven sonata movements →
Beethoven's Ninth. Corpus files are test assets, checked in with the suite.
Done when: the suite runs in CI against the reference decoder; the corpus
exists as raw symbolic source for the compressor's ladder.

### T4 — Renderer (event stream → audio)
GM-soundfont tier first, behind the swappable renderer contract (sample tier
and neural tier are later plugins). CLI: `muse play file.muse [--rendition r]
[--params k=v]`.
Done when: any conforming program renders audible audio offline, no model
required; two parameter sets of the same work are audibly different.

### T5 — AI compressor
MIDI/MusicXML → `program.mu` via the compress → expand → diff → adjust loop:
LLM drafts the program, the reference decoder expands it, the diff metric
(event-stream recall/precision against the parsed source) scores it, feedback
iterates. Provenance of every AI inference recorded in the manifest.
Done when: a Bach chorale round-trips at target fidelity; the metric is
numeric and reported per work; the corpus ladder runs in CI up to whatever
rung currently passes.

### T6 — Player UI
Rendition picker, voice-model (renderer) picker, parameter steering within
sanctioned ranges, baked-performance playback for zero-compute first listen.
Done when: a listener can open a `.muse` file, switch renditions, steer
parameters, and hear results without leaving the app.

### P1 — Prior-art appendix (parallel, docs-only)
`docs/prior-art-executable.md`: L-systems, bytebeat, fractal compression,
WASM/VM specs, tracker formats, game middleware; why-now analysis. Informs
T1's language design. Done when: cited from FORMAT_SPEC.md.

## Explicitly not (yet)

- Distribution/registry (files move as files)
- Marketplace/licensing operations (manifest fields are the whole v0 answer)
- Neural renderer plugins (T4 contract leaves the door open; nothing built)
