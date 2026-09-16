"""Netlify is fully retired from this repo (2026-09-16).

The QA site auto-deployed the `dev` branch for three weeks while a
`netlify.toml` comment claimed it was paused — every push started a build at
`context=production` and burned credits. Rather than keep config around for a
deploy nobody needs, Netlify is gone: the config, the Tier 3 live-smoke test,
and the site's builds (stopped at the API level).

Tier 2 already executes every served page, so the hosted deploy added hosting
cost without adding a distinct check. These tests keep the retirement from
silently reversing — cheaply, offline, and without credentials.
"""

import glob
import os
import re

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _live_files(*patterns, include_self=False):
    """Files that describe the *current* system.

    Exempt are records of the past: anything under ``tests/`` (spec files,
    open or closed — a spec documents intended work, not the running system),
    ``bugs/closed_*``, ``blockers/closed_*`` and ``docs/audit/``.

    **Not** exempt: ``blockers/open_*`` and ``bugs/open_*``. Those prefixes
    are lifecycle state, not history — an open blocker describes the system
    as it is now, so it must not be allowed to assert a retired fact.
    """
    for pat in patterns:
        for path in glob.glob(os.path.join(REPO, pat), recursive=True):
            rel = os.path.relpath(path, REPO).replace(os.sep, "/")
            if "/.git/" in rel:
                continue
            if not include_self and rel == "tests/docs/test_netlify_guard.py":
                continue  # this file necessarily names what it forbids
            if rel.startswith(("tests/", "docs/audit/")):
                continue
            base = os.path.basename(rel)
            top = rel.split("/")[0]
            if base.startswith("closed_") and top in ("bugs", "blockers", "tests"):
                continue
            yield rel, path


def test_no_netlify_config_exists():
    assert not os.path.exists(os.path.join(REPO, "netlify.toml")), (
        "netlify.toml is back — the hosted deploy was retired deliberately "
        "(it auto-deployed dev and cost builds). Re-adding it should be a "
        "decided act, with the deploy story written down first."
    )


def test_live_smoke_test_is_gone():
    assert not os.path.exists(
        os.path.join(REPO, "tools", "qa_frontend", "tests", "test_live_smoke.py")
    ), "the Tier 3 live-smoke test is back, but there is no hosted deploy to smoke"


def test_no_workflow_references_netlify_or_deploys():
    for rel, path in _live_files(".github/workflows/*.yml"):
        with open(path, encoding="utf-8") as fh:
            body = fh.read().lower()
        assert "netlify" not in body, f"{rel} references Netlify"
        assert "deploy" not in body, f"{rel} looks like it may deploy"
        assert "repository_dispatch" not in body, (
            f"{rel} has a dispatch hook — that was the retired deploy-trigger path"
        )


def test_no_live_enable_switch_remains():
    """`QA_LIVE=1` was the resume switch for the live smoke. With the deploy
    gone it would be a dangling flag — assert it is not referenced anywhere
    live, so nobody hunts for the job it used to gate."""
    hits = []
    for rel, path in _live_files("**/*.py", "**/*.md", "**/*.yml", "**/*.html"):
        with open(path, encoding="utf-8", errors="replace") as fh:
            if "QA_LIVE" in fh.read():
                hits.append(rel)
    assert not hits, (
        "QA_LIVE still referenced in live files (the live-smoke gate is "
        "retired):\n  " + "\n  ".join(sorted(hits))
    )


def test_no_live_netlify_url_referenced():
    for rel, path in _live_files("**/*.py", "**/*.md", "**/*.yml", "**/*.html"):
        with open(path, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        for m in re.finditer(r"https?://[^\s\"'<>]*netlify[^\s\"'<>]*", body):
            raise AssertionError(f"{rel} still points at a Netlify URL: {m.group(0)}")


def test_docs_do_not_claim_a_paused_deploy():
    """The original lie, generalized: no live doc may describe a hosted deploy
    as merely 'paused' or 'deferred' — either it exists (documented, with how
    it is gated) or it is retired. Anti-rot for the failure that cost credits."""
    offenders = []
    for rel, path in _live_files("docs/**/*.md", "*.md"):
        with open(path, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        for line in body.splitlines():
            low = line.lower()
            if ("netlify" in low or "hosted preview" in low) and (
                "paused" in low or "deferred" in low
            ):
                offenders.append(f"{rel}: {line.strip()[:100]}")
    assert not offenders, (
        "live doc(s) describe a hosted deploy as paused/deferred — that state "
        "is not enforced anywhere, and it was the exact claim that hid real "
        "build spend:\n  " + "\n  ".join(offenders)
    )