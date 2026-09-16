# muse_workbench_runner — W-B5 interactive surface gate

The runner the workbench page talks to. Executes **only** the commands
committed in `workbench.config.json`'s allow-list, via subprocess with
cwd=repo root, shell=False. Fails closed on missing/malformed config.

## Commands mapped

| Name | Entry |
|---|---|
| `muse_seed.validate` | `tools/muse_seed_cli/cli.py validate` |
| `muse_seed.create` | `tools/muse_seed/cli.py create` |
| `muse_probes.run` | `tools/muse_probes/cli.py` |
| `muse_grow.iterate` | `tools/muse_grow/cli.py` |
| `muse_play.render` | `python3 tools/muse_play/__main__.py` |
| `muse_analyze.run` | `tools/muse_analyze/cli.py` |
| `muse_diff.run` | `tools/muse_diff/cli.py` |
| `muse_tests.fast` | `bash tools/run_tests.sh` |

## API

```bash
python3 tools/muse_workbench_runner/server.py --docs --port 9145
```

`--docs` serves the static `docs/` tree **and** `/api` from one origin
(issue #305). Without it the server is API-only, as before.

- `GET /api/commands` → `{commands: [...], error: null|str}`
- `POST /api/run` `{"name": str, "args": [str...]}` → `{ok, argv, stdout, stderr, rc}`

Unknown/disallowed → HTTP 405. Bad request → 400. Success → 200/500 by exit code.

### Why `--docs` exists (one origin, no hardcoded host)

The terminal pane used to hardcode `http://127.0.0.1:9145`. Served over the
hosted/proxied site that resolves to the *visitor's* machine — where nothing
listens — so every call failed (`/api/commands` → 404, `/api/run` → 501).
Serving the pages and the API from one origin removes the guess entirely, and
the page resolves its runner URL origin-relatively.

Run it with `--docs`, then open the page from the runner's own origin:

```
http://127.0.0.1:9145/workbench/terminal.html
```

Overrides, if the runner must live elsewhere (all optional, no file edit):

| Mechanism | Example |
|---|---|
| query parameter | `terminal.html?runner=http://host:9145` |
| meta tag | `<meta name="muse-runner-url" content="http://host:9145">` |
| window global | `window.MUSE_RUNNER_URL = 'http://host:9145'` |

Precedence: `?runner=` > `window.MUSE_RUNNER_URL` > meta > same-origin.

### Cross-origin (issue #316)

An override pointing at a **different origin** needs that origin allowed on
the runner, or the browser refuses the response:

```bash
python3 tools/muse_workbench_runner/server.py --docs --port 9145 \
    --allow-origin https://work-1.example.dev
```

`--allow-origin` is repeatable, matched **exactly** (no wildcard, no
subdomain or prefix matching), and **off by default**. When set, the server
warns at startup. This is deliberately not the default: the runner executes
allow-listed commands, so any origin granted access can drive them from a
page the user merely visits -- binding to `127.0.0.1` does not prevent that,
because the browser is the confused deputy. Responses always carry
`Vary: Origin`; preflight (`OPTIONS`) is answered only for an allowed origin
and refused with 403 otherwise.

For most use the simplest path is **no override at all**: run the page from
the runner's own origin (`--docs` above), which needs no CORS and is what the
tests exercise by default.

The server still binds `127.0.0.1` only; exposing it beyond the machine is a
deliberate, separate step. Static serving carries a path-traversal guard,
streams large files in chunks rather than buffering them, and never shadows
`/api/*`.

## Dependencies

stdlib only (`json`, `os`, `subprocess`, `http.server`).

## Tests

`cd tools && python -m pytest muse_workbench_runner/tests -q` → 21 tests
(allow-list enforcement, fail-closed config, exec, same-origin static
serving incl. traversal guard).
Registered in `tools/run_tests.sh` fast tier.
