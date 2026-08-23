# Test spec (closed): transient backoff + attempt budget (issue #121)

**Coverage landed in `tests/interpreter-transient.test.mjs`** (7 pins,
canned fetch — no live calls), run via `npm test`:

- Adapter tagging: 503/429 → `err.transient === true`; 400 → terminal.
- 503,503 → success: backoff retries inside a single validation attempt
  (3 calls, `attempts === 1`); the attempt budget is not burned.
- Backoff exhausted: the provider error (status + body) surfaces loudly,
  not swallowed into validation feedback.
- Non-transient error: no transient retry, one call per attempt.
- `MUSE_MAX_ATTEMPTS=1` bounds the loop when `maxAttempts` isn't passed.
