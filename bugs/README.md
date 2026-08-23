# bugs/ — the bug log

One file per defect found in flight, so the human and later agents can
review what's broken without leaving the codebase. **Review this directory
the same way you review `blockers/` and the task queue** — an `open_*`
file here is live work the same way an open blocker or a
`status:available` issue is.

## What goes here (and what doesn't)

- **Bugs** are defects in existing behavior: code that fails, lies, or
  silently does the wrong thing (a runner that reports PASS on failing
  suites, a test suite that only passes from one directory).
- **Blockers** are spec-level ambiguity that stops a task (missing or
  contradictory information only the human can resolve) — those stay in
  `blockers/`.
- **Tasks** are new work. If a bug needs a fix of any size, the log entry
  points at a filed issue; the issue carries the fix.

Rule of thumb: found something broken while doing other work? Log it here
at once, file the `status:available` issue, and get back to your claimed
task. Don't fix out-of-scope bugs inside an unrelated claim.

## Lifecycle

1. Write `bugs/open_YYYYMMDD-HHMMSS_<short-slug>.md` — symptom, repro,
   root cause (if known), and a link to the filed issue.
2. File the issue `status:available` (or comment on the owning in-flight
   issue, if one exists — note that in the log entry).
3. Whoever lands the fix renames the file to
   `bugs/closed_YYYYMMDD-HHMMSS_<short-slug>.md`, appending the fixing
   commit.
4. Fixes are claimed and worked like any other task (TASK_WORKFLOW);
   a bug log entry is not a claim.

No index file — the directory listing is the index, same as `blockers/`.
