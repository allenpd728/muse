# Test spec — B5 technical appendix + decision asks (docs/boardroom/appendix.html, asks.html) — CLOSED

**Resolution (Tests: #272, verified 2026-08-26, run=20260825-2247-qogi):**
the B5 commit (9a66072) shipped
`tools/qa_frontend/tests/test_boardroom_appendix_asks.py` — 5 source-scan
tests covering all spec items: the four topics with correct substance
(P3 conformance/golden vectors, D20 "never leaves the pipeline", D7
"No model training", D11 "ear gates quality"), decision anchors
(D20/D7/D11), the meta-D20 no-leak test, the three asks with anchors,
and read-only (no forms). Verified: `cd tools && python -m pytest
qa_frontend/tests/test_boardroom_appendix_asks.py -q` → 5 passed.

## Behaviors to verify

- **Appendix** covers: conformance (P3 golden vectors), mockup confidentiality (D20 — text must say the mockup never leaves the pipeline), no-training constraint (D7 — stock swappable model), quality-gate philosophy (D11 — ear gates, metrics support).
- **Appendix D20 check**: asserts D20's substance is described while also asserting NO mockup artifact is embedded (the meta-D20 test: the page about confidentiality must not itself leak).
- **Asks page**: three asks present — (a) event-first strategy + budget shape, (b) confirm open-at-launch posture (D4 stands), (c) schedule the E3 publication-surface decision. Each ask references its decision-log/issue anchor (#211 for E3; D4 for the posture).
- **Zero console errors** on both pages.

## Invocation

`cd tools && python -m pytest qa_frontend/tests/test_boardroom_appendix_asks.py -q`
