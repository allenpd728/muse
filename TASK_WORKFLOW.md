# TASK_WORKFLOW.md — Multi-agent task coordination

How agents find, claim, and complete work on Muse. One task = one GitHub issue.
Agents read this document once; everything else they learn from the issues and the
`blockers/` directory.

> **System of record:** the issue queue plus `git log origin/dev`. Status tables in
> docs (pipeline.md etc.) are caches updated by sweeps and may lag — check the queue
> and dev history before concluding work is undone.

## Run-ids

Every agent session generates a **run-id** at session start:
`<YYYYMMDD-HHMM>-<4 random alphanumerics>` (e.g. `20260823-1845-a1b2`). The run-id
appears in every claim comment, done comment, and blocker the session writes. It is
the only way to distinguish claims under a shared GitHub identity — all agents
authenticate as the same account, so labels, assignees, and author fields cannot
tell claims apart. Without run-ids the re-fetch check in §Claiming has no teeth
(2026-08-23: four double-claims in one day).

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

**Documentation deliverable.** Every code task produces a `.md` doc alongside
its code: a README in the tool's directory (usage, API, dependencies) plus a
test spec in `tests/`. The doc is part of the Definition of Done, not an
afterthought. Design docs live in `docs/design/`; user-facing docs live with
the code.

The standing task list is [`docs/pipeline.md`](docs/pipeline.md) (W/S/P/C/L
series). Issues are filed from that list, one per task; sub-tasks are
decomposed from issues that prove too large, not pre-planned beyond the list.

Sizing rule: one task = completable in one agent run (well under an hour of work).
If a task can't be done in one run, it gets decomposed further before becoming
`available`.

## Dependencies

Dependencies are expressed as GitHub "blocked by" relationships, forming lineages.
A task becomes `available` only when **every** issue blocking it is `status:done`
(merged — not merely in review). Within a lineage, only one task is ever available
at a time.

## Claiming protocol

The claim lock applies to **any issue an agent is actively working** — a task, a
`Tests:` follow-up, or a blocker-resolution — not just tasks. The mechanics are
identical for all three; only the "done" action differs.

1. **Sweep stale claims.** Before selecting work, list all `status:claimed` issues.
   For each, if the claim comment is older than **1 hour** with no activity since
   (no commits on the PR, no new comments), the claim is void: remove
   `status:claimed`, restore the prior label (`status:available` for tasks/tests,
   `status:blocked-needs-input` for blockers), and comment that the work was
   reclaimed (audit trail). A fresh claim comment carrying a run-id that is not
   yours belongs to a live sibling — leave it alone; freshness is judged by the
   comment timestamp, never by assuming authorship.
1a. **Sweep protocol violations.** An issue carrying two status labels at once
   (e.g. `status:claimed` + `status:blocked-needs-input`) is in an illegal state
   from a non-atomic edit. The sweep repairs it: the *older* label wins
   (`blocked-needs-input` outranks `claimed` — a blocker claim beats a bare claim),
   the extra label is removed, and a comment records the repair.
1b. **Docs coherence sweep.** Check that `README.md`, `AGENTS.md`,
   `FORMAT_SPEC.md`, [`docs/pipeline.md`](docs/pipeline.md), and
   `corpus/README.md` agree with each other: if a recently-closed task changed
   the design, the plan, or the task list, the sibling docs must reflect it in
   the same session — a stale doc is a process failure on par with a stale
   claim. If something is wrong and no task covers fixing it, file the task.
2. **Pick work.** Any `status:available` issue the agent has enough context to
   start. Default order: lowest issue number first; issues labeled `priority:high`
   jump the queue. Before concluding any work item is undone, check
   `git log origin/dev` and the issue queue — docs tables lag (§System of record);
   dev history does not.
2a. **Filing is not atomic — search, file, search again.** Before filing a new
   task, search open issues for its slug. After filing, search again: if a twin
   with a **lower issue number** now exists, close yours as duplicate with a link
   to it. Self-healing; requires no coordination. (2026-08-23: W3 filed twice as
   #131/#132 within one minute.)
3. **When no task is available, fall through in priority order:**
   - **(a) Open `Tests:` issues.** Claim and complete them one at a time, lowest
     issue number first — writing the tests their spec calls for.
   - **(b) Open PRs with unaddressed review comments.** Fetch review comments
     via the API, address each one (fix + push to the PR branch), reply to
     every thread with the fixing commit, mark threads resolved. The PR is the
     review surface; unaddressed comments are open work.
   - **(c) Open blockers.** If no `Tests:` issues remain, work through
     `status:blocked-needs-input` issues one at a time: attempt to resolve the
     blocker (the spec may have been amended since it was filed), and if
     resolvable, close the blocker and return the task to `status:available`.
   - Only when tasks, `Tests:` issues, PR comments, and blockers are all
     exhausted is the queue empty and the session done.
4. **Attempt the claim, then verify ownership.** Whatever the work item: swap its
   current label to `status:claimed` (from `status:available` for tasks/tests, from
   `status:blocked-needs-input` for blockers) **in one atomic edit — one remove,
   one add, ending with exactly one status label** — self-assign, and post a claim
   comment (`claimed by <agent-name> run=<run-id> at <UTC timestamp>`). Then
   re-fetch the issue **and read the latest claim comment**: if its run-id is not
   yours, a sibling won — back off and pick a different item. Under a shared
   GitHub identity the label/assignee check cannot decide this (both agents set
   the same values); the run-id in the newest claim comment is the tiebreaker.
5. **Do the work; prove the done.** Commit directly to `dev` (no PR — review
   happens retrospectively on `dev`). Swap `status:claimed` → `status:done` and
   close the issue with a comment linking the commits. **Tasks with known-answer
   criteria (conformance counts, golden commands) close only when the done
   comment includes the gate command and its output** — a done claim without
   evidence is how full maps shipped empty and nobody noticed (2026-08-23 W1).
   For a **blocker-resolution** item the "done" action differs: resolve the
   ambiguity (amend the spec/docs), rename the `blockers/open_*` file to
   `closed_*` appending the resolution, remove `status:claimed` from the blocked
   issue, and return that issue to `status:available` — the blocker itself is a
   means, the goal is unblocking the original task.

   **Concurrent-work rules** (agents run in parallel against `dev`):
   - Pull before you start, and again before you push.
   - On push rejection (non-fast-forward): `git pull --rebase origin dev`, resolve
     any conflicts, push again. Repeat as needed.
   - **Rebase revealed a sibling landed the same work?** Compare the two
     implementations: if yours adds nothing, drop it and (if the landed work
     has gaps) file a review follow-up instead of reopening; if yours
     genuinely extends it, merge the two in the rebase. Never push a second
     copy of an already-landed tool.
   - **Never force-push to `dev`** — it can destroy a sibling agent's committed
     work. This is the one move the direct-to-dev model depends on forbidding.
   - A rebase conflict you cannot resolve confidently is a blocker — someone
     else's work changed the ground under your task. Don't guess; file it.
   - Prefer tasks whose touched files don't overlap a sibling's in-flight work;
     when both edit the same file (e.g. different sections of a spec), the rebase
     is usually clean, but confirm the merged result still makes sense before
     pushing.
6. **Spec the tests.** Before closing out, write
   `tests/open_YYYYMMDD-HHMMSS_<task-slug>.md` describing the test coverage the
   work needs: behaviors to verify, edge cases, and how to invoke the tests.
   If the task introduced a behavior with no existing test coverage, the test
   spec is mandatory, not optional. Then file a follow-up GitHub issue titled
   `Tests: <task title>` that links the test spec file, labels it
   `status:available`, and mark it `Blocked by` the task just completed.
   Completed task + filed test spec + linked test issue = a full unit of work.
7. **Unblock dependents.** Before finishing, check the issues that listed this
   task under "Blocked by". For each whose blockers are all now `status:done`,
   label it `status:available` and comment that it is unblocked. Dependent tasks
   do not become visible to the queue on their own — closing without this step
   silently strands them.
8. **Iterate.** If review later finds the work lacking, write a new task rather
   than reopening the old one.

## Test follow-ups

Tests are specified per task, not assumed. The lifecycle mirrors blockers:

- `tests/open_*.md` — a pending test spec: what the task's work must be verified
  against. Written by the completing agent; picked up by a later agent as a
  normal `status:available` task.
- `tests/closed_*.md` — the test issue is `status:done`; the spec file records
  what coverage landed (test file paths, command to run).

Test-spec issues are claimed, worked, and closed like any other task: commit the
tests to `dev`, ensure the repo's test command (stated in `AGENTS.md` →
Build/test, or in the task itself) runs them in CI, then close. A task that
lands code but whose test follow-up never completes is a process failure to
surface in the end-of-session report.

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

**Nested blockers.** Any claimed work item can be blocked, including a `Tests:`
issue — file a blocker pointing at it and swap it to `status:blocked-needs-input`
as usual. The exception is blocker-resolution itself: an agent that cannot
resolve a blocker must **not** file a blocker-on-a-blocker and walk away (that
silent stall strands the queue). Instead: leave the issue
`status:blocked-needs-input`, comment on the issue explaining what is still
missing, and **flag it to the human in the end-of-session report** — blockers are
the one work type where "I can't" escalates to a person, not another layer.
A blocker that resists resolution usually means the underlying task is
under-scoped; recommend splitting it in the report rather than building a
blocker-dependency graph. If the fallback finds open blockers but none are
resolvable, report the queue as **stalled** — do not manufacture busywork.

Resolving a blocker: the human answers on the issue or updates the spec. During
the start-of-session sweep, agents check every `blockers/open_*` file whose issue
has been updated since the file was written; if the blocker is resolved, the agent
renames the file to `closed_YYYYMMDD-HHMMSS_<short-slug>.md` (appending the
resolution), removes `status:blocked-needs-input`, and returns the task to
`status:available`. Closures are reported in the session summary for confirmation.

## End-of-session report

Before finishing, every agent reports (with its run-id):

- Tasks completed (with commit links), including the gate evidence for any
  known-answer DoDs
- Test specs written (linked `Tests:` issues) and any completed tasks whose test
  follow-up never landed
- Stale claims reclaimed during the sweep
- Protocol violations repaired (issues found with two status labels)
- Duplicate filings closed (twins with lower issue numbers surviving)
- Work dropped at rebase because a sibling landed it first (so review knows
  the duplicate existed and was discarded, not lost)
- New blockers written (with one-line reasons)
- Open blockers still awaiting human input
- Blockers closed during the sweep
- Unresolvable blockers escalated, or **stalled queue** if nothing was workable

