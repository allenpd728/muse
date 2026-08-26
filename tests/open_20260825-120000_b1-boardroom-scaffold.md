# Test spec — B1 boardroom scaffold (docs/boardroom/)

## Behaviors to verify

- **Pages exist and render**: deck.html, status.html, competitive.html, appendix.html, asks.html each served at /boardroom/<name>.html with HTTP 200 (qa_frontend convention).
- **Master index links**: docs/index.html nav gains a /boardroom/ entry; the five pages linked from the boardroom landing.
- **Zero console errors** on each page (standard Tier-2 bar).
- **Read-only**: no page mutates; no forms, no buttons that write. (Assertion: no <form> elements; no fetch() with non-GET methods in page source scan.)
- **D20 compliance**: page source scan asserts no mockup JSON content, no `tempo_map` arrays with per-note device fields, no links to *.mockup.json artifacts.

## Invocation

`cd tools && python -m pytest qa_frontend/tests/test_boardroom_scaffold.py -q` (slow tier if Playwright; source-scan tests can be fast tier).
