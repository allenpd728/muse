# muse_author — C2: AI-assisted authoring workbench

LLM analyzes IR → proposes a seed. Generate → validate → fix loop,
validated by C1's validator. Human review approves each iteration.
Design doc: [docs/design/c2-ai-assisted-authoring.md](../../docs/design/c2-ai-assisted-authoring.md).

## Usage

```bash
python3 tools/muse_author/cli.py <work> [--era classical|romantic|...]
```

Proposes a seed per C1/#148 validator's schema; end-to-end exit 0 when
validated against source work.

## Architecture

Deterministic stub emits era-calibrated tempo bounds, philosophy lists per
sibling S3.3 spec (with provenance author/ai_assisted), register + tempo
assertions wrapped into C1's validator (schema → assertions → budgets → exit).

## Tests

Test spec: [tests/open_20260823-223000_c2-authoring.md](../../tests/open_20260823-223000_c2-authoring.md).
