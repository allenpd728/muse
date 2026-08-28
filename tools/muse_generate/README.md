# muse_generate — L1 generate-validate-fix loop

The loop that turns seed + work into a schema-valid mockup:
assemble prompt → provider → validate → retry on violations (bounded).

The deterministic promise: the seed defines the boundary; the provider
interprets; the schema enforces. This is the generate→validate→fix
contract the workbench depends on.

## API

**`assemble_prompt(seed, work, era='baroque', prior_violation=None)`** —
builds the LLM prompt from the seed + work structure. Prior violations
annotate the feedback clause on retry.

**`generate_mockup(seed, work, provider, era='baroque', max_attempts=3)`**
— run the loop, return (mockup_dict, attempts). Fails loudly on
exhaustion.

**`_validate(mockup, work)`** — mockup must satisfy the schema and the
work's assertions before it leaves the loop.

**`GenerateError`** (ValueError) with violation metadata; provider-specific
errors come through as its root cause.

## Usage

```python
from muse_generate import assemble_prompt, generate_mockup
from muse_provider import RecordedProvider

# in tests
p = RecordedProvider({str(hash(assemble_prompt(seed, work))): mockup_dict})
result, attempts = generate_mockup(seed, work, p)
```

## Errors

`GenerateError` (ValueError) with violation details attached.

## Tests

`cd tools/muse_generate && python3 -m pytest -q` — 10 passing, fixture
replay only (RecordedProvider), no network.
