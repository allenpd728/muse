# Test spec — B4 competitive/moat memo (docs/boardroom/competitive.html)

## Behaviors to verify

- **Tool table present** with the re-survey rows: Ableton Live 12, Logic Pro (Session Players), FL Studio (Gopher AI), Suno Studio, and the research line (Basis Mixer / VirtuosoNet / S2A / Midi-LLM).
- **The claim sentence**: "score-aware AI interpretation ships nowhere" (or close paraphrase) present — the memo's load-bearing claim, pinned so a future edit can't quietly soften it.
- **Legal section**: post-settlement licensed future + human-authored-schema copyrightability point present.
- **Risk register**: label walled gardens, patent FTO (Endel/LifeScore/Reactional), niche composer-tool adoption — all named.
- **Source link** to PRIOR_ART_REVIEW.md appendix present.
- **Zero console errors.**

## Invocation

`cd tools && python -m pytest qa_frontend/tests/test_boardroom_competitive.py -q`

## Closed 2026-08-26 (#266, run=20260825-1033-cae1)

Memo landed: the pinned claim ("score-aware AI interpretation ships
nowhere"), the tool table (Ableton/Logic/FL/Pro Tools/Cubase+Studio
One/BandLab/Suno Studio + the research line Basis Mixer/VirtuosoNet/
S2A/Midi-LLM), why text-to-audio can't occupy the interpretation axis,
the legal environment (post-settlement licensed future + schema-first
as legal asset), and the risk register (label walled gardens, patent
FTO incl. Endel/LifeScore/Reactional, niche adoption). Source link to
PRIOR_ART_REVIEW.md.

Tests: tools/qa_frontend/tests/test_boardroom_competitive.py (6) — table
rows, claim pinned, legal section, named risks, source link, zero
console errors.
