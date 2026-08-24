# Bug — .gitignore swallows new .github/ files (CI work silently untracked)

**Found:** 2026-08-24, run=20260823-2312-h8pk, while attempting blocker #194
(workflow-scope token).
**Disposition:** this entry is backed by blocker #194 (workflow-scope);
the .gitignore rule itself needs a human decision.

## Symptom

`.gitignore` contains the rule `.github/`. `conformance.yml` is tracked
anyway (force-added historically), but any *new* workflow file — e.g. the
`live-smoke.yml` a sibling tried to land for #184 — is skipped silently by
plain `git add .github/workflows/live-smoke.yml` ("the following paths are
ignored"). The file never enters the commit, and `git status` shows
nothing. CI work looks committed locally and is not.

## Repro

```bash
git checkout -b probe && touch .github/workflows/x.yml
git add .github/workflows/x.yml
# → "The following paths are ignored by one of your .gitignore files"
git status --short   # → clean; the file is silently skipped
```

## Root cause

`.gitignore` line 6: `.github/`. Repo knowingly carries
`.github/workflows/conformance.yml`, so the rule's intent is unclear —
either it predates CI (then it's obsolete) or it guards something else.

## Fix (one of)

- Narrow the rule — e.g. replace `.github/` with whatever it was meant to
  exclude and add `!.github/workflows/`; or
- Delete the rule — conformance.yml already lives under .github/workflows.

## Impact

Combined with blocker #194: even after a workflow-scope token arrives,
new workflow files will be silently skipped unless every agent remembers
`git add -f`. Documented in the #194 comment; decision belongs to the
human, so this sits as an open entry until the rule is settled.
