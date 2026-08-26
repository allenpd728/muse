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
