"""Route contract for the workbench pages (issue #229; prevents recurrence
of the W-B6 rename breakage, bugs/open_20260824-114500).

The pages moved from `/workbench/` (index.html) to explicit routes
(`detail.html`, `files.html`, `terminal.html`) in 419594f. These tests pin
that contract: bare `/workbench/` is a directory listing (not a page), the
three real routes serve HTML, and every workbench test targets a real
route.
"""

import os
import sys
import urllib.request

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")

WORKBENCH_ROUTES = ["/workbench/detail.html", "/workbench/files.html", "/workbench/terminal.html"]


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def test_bare_workbench_path_is_not_a_page(server):
    """`/workbench/` must NOT silently serve as a page again — if an
    index.html master shell lands (W-B6 lineage), flip this test to assert
    the shell's content instead of the listing."""
    with urllib.request.urlopen(server.url + "/workbench/") as r:
        body = r.read().decode()
    assert "Directory listing for /workbench/" in body


@pytest.mark.parametrize("route", WORKBENCH_ROUTES)
def test_workbench_route_serves_html(server, route):
    with urllib.request.urlopen(server.url + route) as r:
        body = r.read().decode()
    assert "<html" in body.lower(), f"{route} did not serve an HTML page"


def test_seed_workbench_lives_at_detail_route(server, session):
    """The seed workbench page (its h1) is at detail.html — the rename
    target, pinned so a future route change fails here first."""
    page = session.new_page()
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    assert "seed workbench" in page.inner_text("body").lower()
