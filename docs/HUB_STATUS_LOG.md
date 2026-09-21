# HuB status log (`status_log.jsonl`)

This repo publishes one append-only status snapshot per sweep. The HuB
dashboard (https://philipdallen.github.io/HuB/) fetches
`status_log.jsonl` from this repo's `dev` branch and renders it. This repo is
the writer; HuB only reads.

## What writes it

`tools/hub_sweep.py` — see its module docstring for the design rules. It computes a
snapshot from this repo's own GitHub issues at run time, so the log cannot
drift from the tracker the way a hand-maintained table does. Nothing in it is
hardcoded.

```bash
python3 tools/hub_sweep.py --repo philipdallen/rubato --dry-run   # print, write nothing
python3 tools/hub_sweep.py --repo philipdallen/rubato             # append one snapshot
```

It is normally run by the `hub_sweep` GitHub Actions workflow on a schedule and
on manual dispatch. The workflow file is `.github/workflows/hub_sweep.yml`.
A scheduled run that finds no change appends nothing, so an idle repo does not
grow the log.

## Record format

One JSON object per line; append-only; never rewritten. See HuB's
`PM_STATUS_FRAMEWORK.md` for the full schema. Fields:

- `timestamp` — UTC ISO-8601.
- `flow` — counts derived from this repo's issues: `open_total`, `wip`
  (`status:claimed`), `blocked` (`status:blocked-needs-input`), `available`
  (`status:available`), `needs_review`, `blocked_ratio`,
  `cycle_time_median_hours`, `closed_last_30d`, and
  `stale_reversions_since_last` (claims stale per
  `MULTI_AGENT_WORKFLOW.md`: claim comment older than 1 hour with no activity
  since).
- `notes` — the same counts as a one-line human-readable summary.
- `trl` — *only present if* `status/trl.json` exists at the repo root. TRL is a human
  judgement about a component's readiness and cannot be derived from issue counts, so it is
  never guessed: an absent file means the field is omitted and HuB shows its
  "No TRL entries" message. **That is the correct state until someone sets real levels**, not
  a bug to work around.

  What each level means is defined once, for all repos, in HuB's
  [`PM_STATUS_FRAMEWORK.md`](https://github.com/philipdallen/HuB/blob/main/PM_STATUS_FRAMEWORK.md)
  §"What TRL means here". Read it before setting a number — in particular: rate the weakest
  real capability, a component can move *down*, and TRL measures readiness of the *piece*, not
  confidence in the research hypothesis.

  **To publish:** copy `status/trl.json.template` to `status/trl.json`, replace the `null`s
  with integers 0–9, and commit on this repo's tracked branch. It appears on the dashboard
  after the next sweep (nominally every 30 min, but GitHub throttles scheduled runs: observed ~7 runs/24h, median gap 2.3-2.7h, worst 6.3h; plus ~5 min CDN lag). Existing characters in the log are
  never rewritten; only new snapshots carry the values.

  **Candidate components for muse** — drawn from this repo's own docs, not invented.
  Rename, merge, or drop any of these; the list is a starting point, not a contract:

  - **Format spec v1.0** — `.mu` = score + prompt + manifest (`FORMAT_SPEC.md`). Not frozen yet — "tools before spec freeze".
  - **Deterministic player** — P-series — "our MIDI player", the free baseline.
  - **LLM player** — L-series — the product. Proprietary.
  - **Toolchain (W/S/C series)** — `tools/` — analysis workbench, seed workbench. Phase 0 items W1-W5 are done (`docs/pipeline.md`).
  - **Corpus / ratchet** — `corpus/` — Bach to Beethoven 9 (`corpus/README.md`).

  **How to arrive at a level for this repo.** The level is not a vibe — it is read off a
  structure this repo already maintains:

  Derive levels from **`docs/pipeline.md`** — the phase tables and their explicit
  'done when' criteria. Concretely: a task marked **done** and covered by the conformance
  runner (`tools/run_tests.sh`, CI) is level 4; a phase whose **done-when** criterion is met
  is level 6. Muse's own own-vs-product split is relevant: the deterministic player
  (`P-series`) is the free baseline and the LLM player (`L-series`) is the product, so they
  should be rated separately, not averaged.

  Muse's build status lives in `docs/pipeline.md` (the W/S/P/C/L task series) and is the authoritative work plan. TRL here should describe how *usable* a piece is, which for muse can differ sharply from whether it is done — the deterministic player may be usable well before the LLM player is.

  **Do not name a component after an internal task or issue.** Name the capability you would
  hand to someone else — that is what makes the level meaningful to a reader outside this repo.

## Tests

```bash
python3 {test}
```

They are offline and stdlib-only — no network, no token. They cover the
claim-staleness rule, the flow counts, TRL handling, and the append-only /
no-duplicate guarantees.
