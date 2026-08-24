# Literature review — drift and slipping risks (2026-08-24)

Timed review: are we converging with research, and is drift slipping in?

## 1. IR: Partitura vs custom arrays — medium risk

[1] Partitura offers richer fields and alignment utilities; custom arrays are
simpler and have less expressive fidelity. **Risk:** changes or prunes fields
silently change model inputs/labels. Guard: canonical Partitura schema;
round-trip parse checks; per-field presence/change-rate telemetry.

## 2. Pattern discovery: SIATEC vs suffix-array — high risk

[3,4,5,6] COSIATEC/SIATEC finds maximal translational patterns (geometric
compression); suffix-array catches linear monophonic runs. **Risk:** worst-
case cubic runtime + implementation approximations vs linear robustness.
Guard: cross-compare patterns on benchmark (we already have this via W3
SIATEC vs W6 scale budget); monitor pattern coverage + resource telemetry.

## 3. Format round-tripping: MusicXML vs Humdrum/kern — high risk

[8,9,10] Humdrum/kern is the OMR-preferred minimal format; MusicXML is the
ecosystem interchange. **Risk:** format conversions lose up to 5% articulation
and 30% modifiers (MEC study). Guard: MusicXML is canonical for us; kern is
optional; test conversions on a corpus.

## 4. LLM tokenization: REMI/MidiTok vs direct arrays — high risk

[12,13,14] REMI/REMI-z reduce token counts vs direct arrays; adaptive
tokenization creates drift. **Risk:** tokenization choices materially change
model metrics (Note F1, Voice WER). Guard: lock tokenization policy;
contract tests; determine log counts and vocabulary drift.

## 5. LLM conductor interface: structured vs free-form — medium risk

[15,16,17,18] ScoreSpeak/CLAMP2 schemas enforce structure; free-form is high
hallucination risk unless reinforced by validation. **Risk:** schema
validation failure rates + post-hoc corrections. Guard: adopt ScoreSpeak/CLAMP
2 schema validation + a "judge"/reconciliation step (retries bounded by C1
validator).

## 6. Alignment datasets — low-medium risk

[19,20,21,22] Vienna 4x22, Batik/Magaloff, BSED, ASMD aggregations have
varied scope; dataset swaps without provenance cause representational drift.
Guard: dataset provenance + provenance + license; alignment QA in CI.

## Open questions to pivot as measured

- [23] ASMD for multi-corpus alignment expansion
- OMR round-trip benchmarks across styles (we lack)
- Tokenization drift quantification on downstream model outputs
