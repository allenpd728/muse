# F1 — Form curve: windowed compressibility as structural/expressive signal

**Status: tasks filed (2026-08-28): F1 #296 available, F2 #297 + F3 #298
blocked on F1. Design doc (F-series root).** Claude's proposal (adapted from the conversation
above; citations to existing code). The "form curve" is a per-window
compressibility/pattern-density curve across a work, quantized into a
letter-sequence (A = repetitive/compressible, B = moderate, C = dense/novel)
— the form's dramatic shape, made measurable.

Claude's core framing, which this spec accepts: **this is an
evidence/assertion layer, not a generation target.** It measures a
symptom of good interpretation (expressive variation tracking structural
density) and bounds/flags suspicious output — the LLM does the interpretive
work; the curve checks it. Anything the curve feeds directly into the
generation prompt becomes a metric to game (mechanically varying tempo on
schedule). Kept exactly that shape.

## What exists that *is* the compressibility analysis (verified)

- **W3 pattern analyzer** (`tools/muse_analyze/patterns.py"): four detector
  classes — `ptn_exact`, `ptn_transposed`, `ptn_ostinato` (S4's shipped
  operators) + `ptn_imitative` (deferred). It already measures local
  redundancy/repetition density; today it aggregates per whole file.
- **The corpus compression gap is a real signal**: Bach chorales → ~10–12%
  of source; Beethoven 9 → 0.24% (FORMAT_SPEC). That gap *is* a
  compressibility signature, used today for operator shipping, not as a
  structural/expressive signal.
- **The detector output carries onsets already**: each detector returns
  `{normalized_pattern: [start_tick, ...]}` — region data exists in the
  `PatternReport` (actual structure) and is only aggregated into counts in
  `summary()`. The gap is *aggregation*, not detection.

## The gap to close: aggregated → windowed

Per §4.6/§5.1 the analyzer sums over the whole work. The form curve needs
the same detectors computed over a sliding tick window, then a local score
per window. Concretely:

1. **Window**: slide a fixed tick window (default: one bar, resolved via the
   IR meter map — the same `bar_onsets` computation R2 already uses; falls
   back to `N beats × ppq` when no meter map) across the work's tick domain.
2. **Local score per window**: pattern-density (fraction of the window's
   tick range covered by at least one detected pattern region — onset
   membership from the three shipped detectors) + byte-compression ratio of
   the window's serialized events (cheap, matches the S2 packing pipeline's
   zlib feasibility).
3. **Quantize**: map the joined score into A/B/C bins (thresholds calibrated
   per work, not hardcoded global).

## The tool: `muse_form` (new), with a `muse_viz` form track (F2)

`tools/muse_form/` computes the curve and emits
`{work, windows: [{start, end, score, letter}], ppq, window_ticks}`; the
analyzer's detectors stay shared (windowed invocation, not a rewrite).
`tools/muse_viz` renders it as a second track under the piano roll (F2) —
a letter-sequence strip colored by A/B/C, aligned to the same tick axis as
the notes. F2 is small because the curve artifact already exists; the
visualizer just draws it.

## Where it plugs in (F3) — evidence, not generation

1. **Seed authoring (S3)**: an evidence-backed answer to "where does
   tension build / where does it release," which informs where tempo/dynamic
   variation ranges widen/narrow. A C-region plausibly wants a *narrower*
   sanctioned range (don't rush unfamiliar material); an A-region a *wider*
   one (performer breathes/rubato there). Defensible, non-speculative —
   satisfies FORMAT_SPEC §2.6's evidence-driven rule.
2. **Assertions (S3.5/§5)**: a concrete checkable structural assertion —
   "the mockup's local dynamic/tempo variance tracks the score's own
   repetition-density curve" — i.e., don't let the LLM smooth the work's
   form into flatter than the work itself. Stronger than prose assertions.
3. **Distiller/growth loop (L4/G1)**: `muse_distill` extracts tempo-curve
   *shape* (flat|arch|wavering); `muse_grow` compares per-trait deltas. A
   form-curve correlation metric gives the loop "did the mockup's
   expressive shape converge toward or diverge from the score's structural
   entropy curve" — a new fitness signal beyond internal consistency.
4. **muse_compare (L3)**: correlation is a clean automatable discriminator
   between two candidate mockups — first-pass signal on which better tracks
   the piece's dramatic architecture, no listening required.

**Caution gate (accepted from Claude):** none of the above asks the LLM to
*hit* the curve. Assertions live in `muse_assert`'s validate path;
distill/compare live in measurement; authoring lives as evidence for the
human encoder. The generation loop's prompt never receives the curve as a
target.

## Format-first review (which of these is sanctioned)

- F1's windowed detectors reuse the S4 operator set — no new operators.
- The curve artifact is a new *tool output* (like the probe JSON), not a
  format field; no FORMAT_SPEC bump.
- The **assertion kind** for F3 IS a format addition
  (`form_curve_correlation` alongside `must_contain`/`register`/`form`/
  `tempo_bounds`) — it amends §5.1 assertively, per the v0 additive rule.
  Flagged here so it isn't hard-coded into `muse_assert` without a spec
  note.

## Task decomposition (ready to file)

| Task | Scope | Blocked by |
|---|---|---|
| **F1 (#296)** | `tools/muse_form`: windowed invocation of W3 detectors + window score + quantization; emits the curve artifact; bar-window resolution via the IR meter map (R2's `bar_onsets`) | none |
| **F2 (#297)** | `muse_viz` form track: letter-sequence strip under the piano roll, tick-aligned | #296 |
| **F3 (#298)** | assertion kind (`form_curve_correlation`) spec note + `muse_assert` wiring; optional distill/compare correlation metric | #296 |

F1 first (eyeball whether Beethoven 5 produces a recognizable
letter-sequence before wiring assertions), exactly as Claude's smallest
step suggests. F3's assertion part amends §5.1, so it lands with a
FORMAT_SPEC note in the same commit, per pin discipline.
