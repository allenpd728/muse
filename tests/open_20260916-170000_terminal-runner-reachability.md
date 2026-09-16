# Test spec — workbench terminal runner reachability (#305)

Written 2026-09-16 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

The terminal pane could not reach its runner when served over the hosted
site: `docs/workbench/terminal.html` hardcoded
`RUNNER_URL = 'http://127.0.0.1:9145'`, which in a proxied browser resolves
to the *visitor's* machine (nothing listening) — `GET /api/commands` → 404,
`POST /api/run` → 501.

Two-sided fix:

1. **`tools/muse_workbench_runner/server.py`** gains optional static serving.
   `serve(port, config_path, docs_dir)` (CLI: `--docs`, `--docs-dir`,
   `--port`) serves the `docs/` tree and `/api` from one origin. The bind
   stays `127.0.0.1`. Static serving has a path-traversal guard and never
   shadows `/api/*`; `docs_dir=None` keeps the previous API-only behavior.
2. **`docs/workbench/terminal.html`** resolves its runner URL
   origin-relatively via `resolveRunnerUrl()` — query `?runner=`, meta
   `muse-runner-url`, or `window.MUSE_RUNNER_URL`, defaulting to same-origin.
   The unreachable-path message now names the correct start command.

Coverage: `tools/qa_frontend/tests/test_terminal_runner_reachability.py`
(10 tests, slow tier) + 7 new tests in
`tools/muse_workbench_runner/tests/test_runner.py` (fast tier).

## Coverage written

**Source tier (fast, no browser).**
1. `RUNNER_URL` is not assigned a literal `127.0.0.1`/`localhost` origin
   (DoD 4b).
2. Override hooks exist (meta tag + `?runner=` query).
3. No `fetch('http://…/api/…')` absolute API URL survives anywhere in the page.

**Live tier (the real page against the real server, one origin).**
4. `GET /api/commands` → 200 over the served origin (DoD 2).
5. `POST /api/run` reaches the route — asserts 405 (allow-list), *not*
   404/501, for a disallowed name (DoD 2).
6. The static page and the API are both served from the same origin.
7. Clicking a DRAWER button produces a `/api/run` response with no 404, no
   501, no runner-unreachable text, and an `rc:` in the output panel (DoD 4a).
   Uses the `diff` entry: `analyze` runs the full corpus and would not
   respond inside the test's patience window.
8. A typed command goes through the prompt path and returns runner JSON (DoD 4a).
9. Zero console errors on a clean load.
10. The docs server rejects path traversal (`/../AGENTS.md` → 404).

**Server tier (fast).**
11. Static page served; API + static on one origin; directory path → index;
    `/api/<unknown>` is not shadowed by the static tree; traversal blocked
    for `/../`, `/../../`, and percent-encoded `/..%2f`; API-only mode when
    `docs_dir` is None; `Content-Type: application/json` on the API.

## Verification that the pins are not vacuous

Re-injecting the old hardcoded URL into `terminal.html` fails three tests —
the source pin plus both live browser tests — and restoring it passes all
ten. The server-branch tests were likewise exercised against the
traversal probes.

## Known gaps (acceptable)

- **The hosted/proxied path itself is not exercised.** These tests drive a
  locally served origin; the real proxy is the paused Netlify deploy (Tier 3
  live smoke, #224, blocked). What is pinned here is the property that makes
  the proxied case work: one origin, no hardcoded host.
- **`--docs` on a non-localhost bind is untested and not offered.** Exposing
  the runner beyond the machine needs an auth decision first (the pane has no
  token concept); `127.0.0.1` binding is unchanged, and AGENTS.md's sandbox
  posture is preserved.
- The era-filter/generate panes on the same page are covered by
  `test_wb10_generate_wire.py` and are unchanged here.

## Closed 2026-09-16 (#305, run=20260916-1525-8d06)

Landed with 17 new/extended tests. `qa_frontend` 128 passed / 5 skipped
(was 118/5); `muse_workbench_runner` 21 passed (was 14); fast tier all 35
suites green.