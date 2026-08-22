# Test spec: import CLI + corpus residual coverage (follow-up to #20)

**Source task:** #20 (test corpus + CLI)
**Code under test:** `importer/cli.mjs` (`tests/import-cli.test.mjs` covers the
DoD: corpus fixtures import end-to-end, magic-byte detection, unknown format
rejection). This spec covers what it does not.

## Behaviors to verify

- **Missing output flag** / missing input arg: usage + exit 1.
- **Output path in a non-existent directory**: readable error, no partial file.
- **`.musicxml` (uncompressed) input**: format detection falls back to extension
  when bytes are not zip/MIDI — corpus needs one plain `.musicxml` file.
- **`.midi` extension** (not just `.mid`): detected as MIDI by extension fallback.
- **Validation failure leaves no artifact**: force a synthesis bug (or use a
  fixture that fails validation) and assert the output path is absent after
  exit 1 — the CLI's "never emit a non-validating document" rule.
- **Corpus growth**: every new file in `importer/fixtures/` that is a real
  corpus entry (`.mid`, `.mxl`, `.musicxml`) is imported in CI — the test
  should enumerate the directory rather than pin a hardcoded list, so adding
  a chorale is adding a file, not editing a test.

## How to run

Extend `tests/import-cli.test.mjs`; `npm test` picks the suite up automatically.
