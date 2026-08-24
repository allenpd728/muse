# Test spec — W-B5 workbench runner (task #232)

## How to invoke

```bash
cd tools && python -m pytest muse_workbench_runner/tests -q
```

## Coverage landed with the task

- Config parse: repo `workbench.config.json` loads, allowlist honored
- Fail closed: missing / malformed / empty allowlist / unknown entry all
  disable the runner with an explicit error string
- Run gate: unknown command → 405, disallowed name → 405, exec captures
  stdout/stderr/rc
- HTTP surface: `/api/commands` lists; `/api/run` honors; bad args → 400,
  other paths → 404
- Command map sanity: every mapped argv head is python3/bash and the tool
  path exists in-repo

## Behaviors still needing coverage (future)

- The Docs sweep if W-B6+ lands: the runner serves only 127.0.0.1
- Config keys tolerated (terminal block validated when W-B8 lands)
