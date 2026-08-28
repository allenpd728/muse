# muse_provider — Pluggable LLM generation adapter

generate(prompt) → dict. Providers:
- **GeminiProvider**: free-tier Gemini API (`GOOGLE_API_KEY`). Live calls
  only when explicitly enabled (tests never touch the network).
- **ManualProvider**: prints the prompt, reads pasted JSON from
  stdin — the no-key fallback (spike-era precedent).
- **RecordedProvider**: deterministic fixture replay for tests and CI.

Generation lacks a network guarantee: providers must fail loudly on
anything unexpected (parse errors, empty responses, timeouts).

## Providers

`GeminiProvider(api_key=None, model=None, live, timeout=180)` — the full-DNA
response is slow; timeouts are long on purpose. Defaults to
`gemini-3-flash-preview` (model rot: re-probe /v1beta/models if a 404 comes
back).

`ManualProvider(input_fn=input, output_fn=print)` — prints → pastes
JSON on stdin — the headless fallback when the founder supplies the output.

`RecordedProvider(responses: {hash(prompt): dict})` — fixture replay; fails
loudly on unrecorded prompt (test fixture must be deliberate, not guessed).

`default_provider(live=False)` — Gemini when GOOGLE_API_KEY and live=True,
otherwise ManualProvider (fail-safe without a key).

## Errors

`ProviderError` (ValueError) on every failure mode: network, parse, empty
response, unknown prompt hash, offline Gemini, missing key.

## Tests

`cd tools/muse_provider && python3 -m pytest -q` — 8 passing, no network
calls, no GOOGLE_API_KEY required (offline/recorded providers only).
