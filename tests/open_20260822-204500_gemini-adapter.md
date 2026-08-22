# Test spec: Gemini adapter residual coverage (follow-up to #106)

**Source task:** #106 (Gemini provider adapter)
**Code under test:** `interpreter/expand.mjs` geminiCall (`tests/interpreter-gemini.test.mjs`
covers DoD: provider resolution, missing-key error, endpoint/structured-JSON/
role wire shape, text surfacing for the retry loop). This spec covers what remains.

## Behaviors to verify

- **Error surface:** a non-OK Gemini response (429 rate limit, 400 bad key)
  produces a readable error that the retry loop can feed back — pin that the
  status + body text land in the thrown error, not swallowed.
- **Retry loop integration:** a Gemini-shaped response that is prose-wrapped
  JSON (a real model behavior) retries with feedback; pin against the canned
  fetch, not a live key.
- **MUSE_BASE_URL override:** `MUSE_BASE_URL` applies to the gemini adapter
  too (proxy/test harness support) — currently untested.
- **Model default:** the spec says default to the current free-tier flash
  model — the implementation requires explicit MUSE_MODEL (no hard-coded
  default, per the model-agnostic rule). Pin the choice in the docs or
  reconcile: either document that MUSE_MODEL is always required, or the
  adapter defaults when provider is gemini.

## How to run

`npm test`; live smoke stays manual (recorded in the closing comment).
