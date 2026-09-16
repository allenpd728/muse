"""Netlify deploy-cost guard (issue #316 side effect).

The QA site auto-deployed the `dev` branch for three weeks while a
`netlify.toml` comment claimed it was "paused" — every push started a build
at `context=production` and burned credits. A stale comment cannot enforce
anything, so this pins the facts that were wrong:

  1. `netlify.toml` must not claim the site is paused/deferred while it is
     configured to build (the exact lie that caused the spend).
  2. The file must document how builds are actually stopped, since the stop
     lives in the Netlify API, not in the repo.

This is a static, offline check (no network): the API-side `stop_builds`
flag cannot be asserted from CI without credentials, so what is pinned here
is that the repo does not *misstate* the situation again.
"""

import os

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
NETLIFY = os.path.join(REPO, "netlify.toml")


def _text():
    with open(NETLIFY, encoding="utf-8") as fh:
        return fh.read()


def test_netlify_toml_does_not_claim_a_pause_that_is_not_enforced():
    """The original bug: a `[DEFERRED]` note asserting the site was paused
    while it was actively deploying dev. If a pause is claimed, the file must
    also say how it is enforced (the API flag), so the claim is checkable."""
    text = _text()
    lowered = text.lower()
    claims_pause = "[deferred" in lowered or "paused" in lowered
    if not claims_pause:
        return  # nothing claimed: nothing to contradict
    assert "stop_builds" in text, (
        "netlify.toml claims the site is paused/deferred but does not state how "
        "that is enforced. A comment cannot stop a deploy — the first version of "
        "this file did exactly that and burned build credits for three weeks. "
        "Either document the API-level stop or drop the claim."
    )


def test_netlify_toml_states_the_current_stopped_state():
    text = _text()
    assert "STOPPED" in text, (
        "netlify.toml no longer records that builds are stopped; without that, "
        "an agent reading the file cannot tell whether pushes cost money"
    )
    assert "84c6f54c-1f65-40bb-99dc-4e4f73730ff3" in text, (
        "the site id must be recorded — the re-enable command is useless "
        "without it"
    )


def test_netlify_toml_documents_how_to_reenable():
    """Resuming must be a deliberate, documented act, not a guess."""
    text = _text()
    assert "stop_builds" in text and "false" in text, (
        "the re-enable path (stop_builds: false) is not documented"
    )


def test_no_workflow_triggers_a_deploy():
    """Nothing in CI should deploy: the deploy gates were intentionally on
    hold, and a workflow that deploys would reintroduce the cost."""
    import glob

    wf_dir = os.path.join(REPO, ".github", "workflows")
    for path in glob.glob(os.path.join(wf_dir, "*.yml")):
        with open(path, encoding="utf-8") as fh:
            body = fh.read().lower()
        assert "netlify" not in body, (
            f"{os.path.basename(path)} references Netlify — deploys are meant "
            f"to be stopped (see netlify.toml)"
        )
        assert "deploy" not in body, (
            f"{os.path.basename(path)} looks like it may deploy"
        )