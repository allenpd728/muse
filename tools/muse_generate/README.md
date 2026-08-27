# muse_generate — L1 generate → validate → fix loop

`assemble_prompt(seed, work)` builds the LLM's instructions from S3 seed
fields + work structure (parts, maps) + era budgets. `generate_mockup`
calls the provider, validates the result against schema v1 + the work's
assertions, and retries up to `max_attempts` with the violation appended
to the prompt. Deterministic with a `RecordedProvider`.

## Usage

```python
from muse_generate import assemble_prompt, generate_mockup
from muse_provider import RecordedProvider

prompt = assemble_prompt(seed, work, era="baroque")
mockup = generate_mockup(seed, work, provider, era="baroque",
                         max_attempts=3)
```

The task is driven by `tools/muse_grow` and the probe engine; direct CLI
access is via those callers, not a standalone entry point here.

## API

- `assemble_prompt(seed, work, era)` → prompt string
- `generate_mockup(seed, work, provider, era, max_attempts)` → mockup
  dict (schema v1 shape) or raises `GenerateError` with the accumulated
  violations
- `_validate(mockup, work)` → None or a violations list (internal)

## Dependencies

`muse_provider` (pluggable provider), `muse_seed` (seed/assertions),
`muse_mockup` (schema validation), `muse_ir` (work). No network calls in
tests — recorded fixtures only.

## Tests

`tools/muse_generate/tests/`. Spec coverage per the L1.3 task (#208).
