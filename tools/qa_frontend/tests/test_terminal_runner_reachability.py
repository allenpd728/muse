"""Workbench terminal runner reachability (issue #305).

The bug: `docs/workbench/terminal.html` hardcoded
`RUNNER_URL = 'http://127.0.0.1:9145'`. Served over the hosted/proxied site
that resolves to the *visitor's* machine, where nothing listens, so every
call failed (GET /api/commands -> 404, POST /api/run -> 501).

The fix: the runner server optionally serves the static `docs/` tree and the
API from **one origin**, and the page resolves its runner URL
origin-relatively (with meta/query/env overrides).

Tier 1 here is a source-scan (fast, no browser) pinning that the hardcoded
origin is gone and remains overridable. Tier 2 drives the real page against
the real runner server on one origin.
"""

import os
import re
import sys
import threading
import urllib.error
import urllib.request

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")
TERMINAL = os.path.join(DOCS, "workbench", "terminal.html")


def _terminal_source():
    with open(TERMINAL, encoding="utf-8") as fh:
        return fh.read()


# --- Tier 1: source contract (no browser) ---

def test_runner_url_is_not_hardcoded_to_localhost():
    """DoD 4b: RUNNER_URL must not be hardcoded to 127.0.0.1."""
    src = _terminal_source()
    # The const must not be assigned a literal 127.0.0.1/localhost origin.
    assert not re.search(
        r"const\s+RUNNER_URL\s*=\s*['\"]https?://(127\.0\.0\.1|localhost)",
        src,
    ), "RUNNER_URL is hardcoded to a localhost origin again"


def test_runner_url_is_configurable():
    """Override hooks exist: meta tag, ?runner= query, or window global."""
    src = _terminal_source()
    assert "muse-runner-url" in src, "no meta override hook"
    assert "runner" in src and "URLSearchParams" in src, "no ?runner= override"


def test_terminal_source_has_no_split_origin_api_call():
    """The page must not build an absolute API URL from a literal origin."""
    src = _terminal_source()
    hits = re.findall(r"fetch\(\s*['\"]https?://[^'\"]*?/api/", src)
    assert not hits, f"absolute API URL(s) in the page: {hits}"


# --- Tier 2: the real page against the real runner, one origin ---

@pytest.fixture(scope="module")
def runner_server():
    sys.path.insert(0, os.path.join(REPO, "tools"))
    from muse_workbench_runner.server import DOCS_DIR, serve

    srv, url = serve(0, None, DOCS_DIR)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield url
    srv.shutdown()


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def test_runner_api_reachable_on_page_origin(runner_server):
    """DoD 2: GET /api/commands returns 200 over the served site."""
    with urllib.request.urlopen(runner_server + "/api/commands") as r:
        assert r.status == 200
        assert b"commands" in r.read()


def test_runner_post_reachable_on_page_origin(runner_server):
    """DoD 2: POST /api/run answers over the served site (405 = not allowed,
    not 501/404 — i.e. the route exists)."""
    body = b'{"name": "definitely.not.allowed", "args": []}'
    req = urllib.request.Request(
        runner_server + "/api/run", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            assert r.status == 200
    except urllib.error.HTTPError as e:
        assert e.code == 405, f"expected the allow-list 405, got {e.code}"


def test_static_page_and_api_share_one_origin(runner_server):
    """Both the page and the API are served from the same origin — the
    property that makes the pane work when proxied."""
    for path in ("/workbench/terminal.html", "/api/commands"):
        with urllib.request.urlopen(runner_server + path) as r:
            assert r.status == 200, f"{path} not served on the runner origin"


def test_static_serving_rejects_path_traversal(runner_server):
    """The docs server must not escape its root (AGENTS.md sits one level up)."""
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(runner_server + "/../AGENTS.md")
    assert e.value.code == 404


def test_drawer_click_succeeds_without_404_or_unreachable(runner_server, session):
    """DoD 4a: load the page against the served+proxied origin, click a
    DRAWER button, assert no network error, no 404, and no
    runner-unreachable text.

    Uses the `diff` drawer entry (`analyze` runs the full corpus and its
    response would not arrive inside the test's patience window)."""
    page = session.new_page()
    api_calls = []
    page.on("response", lambda r: api_calls.append((r.status, r.request.method))
            if "/api/" in r.url else None)
    page.goto(runner_server + "/workbench/terminal.html", wait_until="networkidle")
    with page.expect_response(lambda r: "/api/run" in r.url, timeout=15000) as resp:
        page.locator(".drawer button", has_text="diff").first.click()
    page.wait_for_timeout(300)

    out = page.inner_text("#out").lower()
    assert "runner unreachable" not in out, f"pane reported unreachable: {out[:200]}"
    assert api_calls, "no /api call was made — the pane never reached the runner"
    statuses = {s for s, _ in api_calls}
    assert 404 not in statuses, f"404 from the api: {api_calls}"
    assert 501 not in statuses, f"501 from the api: {api_calls}"
    # The route exists and executed: rc is reported even when the tool itself
    # exits non-zero (a usage error is a healthy runner, not an unreachable one).
    assert resp.value.status != 404
    assert "rc:" in out, f"no runner rc in output: {out[:200]}"


def test_typed_command_runs_through_the_pane(runner_server, session):
    """A typed command goes through the prompt path and returns runner JSON
    (stdout/stderr/rc), not an error banner."""
    page = session.new_page()
    page.goto(runner_server + "/workbench/terminal.html", wait_until="networkidle")
    page.fill("#cmd", "muse_diff.run --help")
    page.click("#run")
    page.wait_for_timeout(2500)
    out = page.inner_text("#out")
    assert "rc:" in out, f"no runner rc in output: {out[:200]}"
    assert "unreachable" not in out.lower()


def test_terminal_page_zero_console_errors(runner_server, session):
    """Clean load, no interactions.

    Nesting a second PageSession is illegal (Playwright sync API inside the
    live sync context — the harness note in test_pipeline_table.py), so this
    reuses the shared session and measures *this page's* errors by clearing
    the buffer first. Sibling tests here deliberately drive a non-zero tool
    exit, which the runner answers with 500 and the browser logs.
    """
    session.console_errors.clear()
    page = session.new_page()
    page.goto(runner_server + "/workbench/terminal.html", wait_until="networkidle")
    page.wait_for_timeout(400)
    errors = [e for e in session.console_errors if "favicon" not in e]
    assert errors == [], errors[:2]