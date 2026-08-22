# TASK_WORKFLOW.md — Multi-agent task coordination

How agents find, claim, and complete work on Muse. One task = one GitHub issue.
Agents read this document once; everything else they learn from the issues and the
`blockers/` directory.

## System of record

- **GitHub Issues + labels** — the live task queue. Claiming is atomic via the API
  (label swaps are serialized server-side; see Claiming).
- **`blockers/` directory in this repo** — one file per blocked task, so the human
  can review what needs input without leaving the codebase.

No `BLOCKERS.md` index file — the directory listing is the index.

## Task states

| Label | Meaning |
|---|---|
| `status:available` | Ready to be claimed. All blockers are `done`. |
| `status:claimed` | An agent has claimed it. Claim comment is the heartbeat. |
| `status:done` | Work committed to `dev`. The human reviews on `dev` at leisure; anything needing changes spawns a follow-up task. |
| `status:blocked-needs-input` | Agent could not start or finish; needs human input. |

## Task definition

Each issue contains:

- **Summary** — what to build, in one paragraph
- **Definition of done** — the observable end state (files written, checks passing)
- **Context** — links to spec sections, prior art, or related tasks the agent needs
- **Blocked by** — native GitHub issue-blocking relationships forming the lineage

Sizing rule: one task = completable in one agent run (well under an hour of work).
If a task can't be done in one run, it gets decomposed further before becoming
`available`.

## Dependencies

Dependencies are expressed as GitHub "blocked by" relationships, forming lineages.
A task becomes `available` only when **every** issue blocking it is `status:done`
(merged — not merely in review). Within a lineage, only one task is ever available
at a time.

## Claiming protocol

1. **Sweep stale claims.** Before selecting work, list all `status:claimed` issues.
   For each, if the claim comment is older than **1 hour** with no activity since
   (no commits on the PR, no new comments), the claim is void: remove
   `status:claimed`, add `status:available`, and comment that the task was
   reclaimed (audit trail).
2. **Pick a task.** Any `status:available` issue the agent has enough context to
   start. Default order: lowest issue number first; issues labeled `priority:high`
   jump the queue.
3. **Attempt the claim.** Add `status:claimed`, self-assign, and post a claim
   comment (`claimed by <run-id> at <UTC timestamp>`). Then re-fetch the issue:
   if the label or assignee doesn't match, another agent won — back off and pick
   a different task. GitHub serializes these writes, so exactly one agent wins.
4. **Do the work.** Commit directly to `dev` (no PR — review happens
   retrospectively on `dev`). Swap `status:claimed` → `status:done` and close the
   issue with a comment linking the commits.
5. **Spec the tests.** Before closing out, write
   `tests/open_YYYYMMDD-HHMMSS_<task-slug>.md` describing the test coverage the
   work needs: behaviors to verify, edge cases, and how to invoke the tests.
   If the task introduced a behavior with no existing test coverage, the test
   spec is mandatory, not optional. Then file a follow-up GitHub issue titled
   `Tests: <task title>` that links the test spec file, labels it
   `status:available`, and mark it `Blocked by` the task just completed.
   Completed task + filed test spec + linked test issue = a full unit of work.
6. **Iterate.** If review later finds the work lacking, write a new task rather
   than reopening the old one.

## Test follow-ups

Tests are specified per task, not assumed. The lifecycle mirrors blockers:

- `tests/open_*.md` — a pending test spec: what the task's work must be verified
  against. Written by the completing agent; picked up by a later agent as a
  normal `status:available` task.
- `tests/closed_*.md` — the test issue is `status:done`; the spec file records
  what coverage landed (test file paths, command to run).

Test-spec issues are claimed, worked, and closed like any other task: commit the
tests to `dev`, ensure `npm test` (or the task's stated command) runs them in CI,
then close. A task that lands code but whose test follow-up never completes is a
process failure to surface in the end-of-session report.

## Blockers

When an agent cannot start or complete a task (unclear spec, missing context,
ambiguous definition of done), it must not guess:

1. Write `blockers/open_YYYYMMDD-HHMMSS_<short-slug>.md` containing:
   - the task/issue attempted
   - what information is missing
   - what is needed to unblock
2. Label the issue `status:blocked-needs-input` and comment with a link to the
   blocker file.
3. Move on to a different available task — never sit idle on a blocker.

**Blocker quality bar.** Blockers are for spec-level ambiguity — missing or
contradictory information that only the human can resolve. They are not for
implementation choices, which are the agent's to make. Before writing one,
confirm:

- You read the relevant spec/docs and can cite the exact gap (quote the section).
- The missing information is a *decision* (what should the format allow?), not a
  *mechanism* (how do I encode it? — that's your job).
- You state what you tried and why it was insufficient.

If you can make a reasonable call and note it in the commit/PR for retrospective
review, do that instead — a blocker is a claim that the work is genuinely
unstartable, not that a choice felt uncertain.

Resolving a blocker: the human answers on the issue or updates the spec. During
the start-of-session sweep, agents check every `blockers/open_*` file whose issue
has been updated since the file was written; if the blocker is resolved, the agent
renames the file to `closed_YYYYMMDD-HHMMSS_<short-slug>.md` (appending the
resolution), removes `status:blocked-needs-input`, and returns the task to
`status:available`. Closures are reported in the session summary for confirmation.

## End-of-session report

Before finishing, every agent reports:

- Tasks completed (with commit links)
- Test specs written (linked `Tests:` issues) and any completed tasks whose test
  follow-up never landed
- Stale claims reclaimed during the sweep
- New blockers written (with one-line reasons)
- Open blockers still awaiting human input
- Blockers closed during the sweep

