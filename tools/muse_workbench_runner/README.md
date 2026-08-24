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

`python3 tools/muse_workbench_runner/server.py` → binds 127.0.0.1:ephemeral.

- `GET /api/commands` → `{commands: [...], error: null|str}`
- `POST /api/run` `{"name": str, "args": [str...]}` → `{ok, argv, stdout, stderr, rc}`

Unknown/disallowed → HTTP 405. Bad request → 400. Success → 200/500 by exit code.

## Dependencies

stdlib only (`json`, `subprocess`, `http.server`).

## Tests

`cd tools && python -m pytest muse_workbench_runner/tests -q` → 14 tests.
Registered in `tools/run_tests.sh` fast tier.
