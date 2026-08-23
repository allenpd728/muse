# TASK_WORKFLOW.md — Multi-agent task coordination (git-based)

How agents find, claim, and complete work on Muse. **One task = one file in
`tasks/`.** No external issue tracker — the repo is the system of record.
Agents read this document once; everything else they learn from the `tasks/`,
`blockers/`, and `tests/` directories.

## System of record

- **`tasks/` directory in this repo** — the live task queue. One file per task,
  state in the filename prefix (same convention as `blockers/` and `tests/`).
- **`blockers/`** — one file per blocked task.
- **`tests/`** — test specs per completed task.
- **`docs/pipeline.md`** — the high-level plan and status board. The task files
  are the discrete parts; pipeline.md is the map.

No GitHub issues, no external tracker. Git history is the audit trail.

## Task states

| Prefix | Meaning |
|---|---|
| `tasks/open_<slug>.md` | Ready to be claimed. All dependencies `done`. |
| `tasks/claimed_<slug>.md` | An agent has claimed it. Claim line in the file is the heartbeat. |
| `tasks/done_<slug>.md` | Work committed. The human reviews at leisure; changes spawn a follow-up task. |
| `tasks/blocked_<slug>.md` | Could not start or finish; paired with a `blockers/open_*` file. |

## Task file format

```markdown
# W1 — Event-stream IR

**Status:** open
**Depends on:** none
**Phase:** 0 (workbench)

## Summary
One paragraph: what to build.

## Definition of done
- The observable end state (files written, checks passing).

## Context
- Links to spec sections, corpus files, related tasks.
```

Sizing rule: one task = completable in one agent run. If it can't be done in
one run, decompose before it becomes `open`.

## Claiming protocol

1. **Sweep stale claims.** List all `tasks/claimed_*` files. If the claim line
   is older than **1 hour** with no commits since, the claim is void: rename
   back to `open_*` and note the reclaim in the file (audit trail).
2. **Docs coherence sweep.** Check README, AGENTS, FORMAT_SPEC, pipeline, and
   corpus README agree with each other and with task states. A stale doc is a
   process failure on par with a stale claim.
3. **Pick work.** Any `open_*` task you have enough context to start. Default
   order: the pipeline's phase order (W → S → P → C → L), lowest number first.
4. **When no task is open, fall through in priority order:**
   - **(a)** Open test specs (`tests/open_*`) — write the tests they call for.
   - **(b)** Open blockers (`blockers/open_*`) — attempt to resolve; if the
     spec has been amended since filing, close the blocker and return the task
     to `open_*`.
   - Only when all three are exhausted is the queue empty and the session done.
5. **Claim.** Rename `open_<slug>.md` → `claimed_<slug>.md`, add a claim line
   (`claimed by <run-id> at <UTC timestamp>`), commit immediately, push. The
   commit is the lock — first push wins; a rejected push means another agent
   got there first, back off and pick a different task.
6. **Do the work.** Commit directly to `dev`. On completion: rename
   `claimed_*` → `done_*`, update the file's status line, update the status
   column in `docs/pipeline.md`, commit with the task slug in the message.
7. **Spec the tests.** Write `tests/open_<datetime>_<slug>.md` describing the
   coverage the work needs. A task that lands code without a test spec is
   incomplete.
8. **Unblock dependents.** Check every task file whose `Depends on` lists this
   one; for each whose dependencies are all now `done_*`, it's newly open —
   say so in the session report. Dependents don't announce themselves.

## Concurrent-work rules (agents run in parallel against `dev`)

- Pull before you start, and again before you push.
- On push rejection: `git pull --rebase origin dev`, resolve, push again.
- **Never force-push to `dev`** — it can destroy a sibling agent's work.
- A rebase conflict you can't resolve confidently is a blocker — file it,
  don't guess.
- Prefer tasks whose touched files don't overlap a sibling's in-flight work.
- Task-file renames are atomic in git; a rename conflict on claim means you
  lost the race — back off cleanly.

## Blockers

When you cannot start or complete a task, do not guess:

1. Write `blockers/open_<datetime>_<slug>.md`: the task attempted, what's
   missing, what's needed to unblock.
2. Rename the task file to `blocked_<slug>.md` and link the blocker in it.
3. Move on to a different open task — never sit idle on a blocker.

**Blocker quality bar.** Blockers are for spec-level ambiguity — decisions only
the human can make, not implementation choices (those are yours). Before
writing one: cite the exact spec gap, state what you tried, state why a
reasonable call isn't safe. If you can make the call and note it in the commit
for retrospective review, do that instead.

**Nested blockers.** Any claimed item can be blocked, including a test spec.
The exception is blocker-resolution itself: never file a blocker on a blocker.
Leave it open, explain what's still missing in the blocker file, and flag it
to the human in the session report. If nothing is workable, report the queue
as **stalled** — do not manufacture busywork.

## End-of-session report

Before finishing, every agent reports:

- Tasks completed (task file renames, commit links)
- Test specs written
- Stale claims reclaimed
- New blockers written (one-line reasons)
- Blockers closed
- Pipeline status updates made
- Unresolvable blockers escalated, or **stalled queue** if nothing was workable
