"""Anchor-fragment resolution + nav follow-ups (issue #313).

The sweep in #310 checks link *paths*. It cannot check `#fragment` targets,
and that is exactly the hole #310's bug lived in: the corpus tree linked
`workbench/detail.html#<fid>` and no such element existed — every href
resolved to an existing *file*, so the path sweep was satisfied while the
fragment went nowhere.

These tests resolve fragments against **rendered** pages, so runtime-built
anchors (the corpus tree's and the workbench's) are covered too — a static
scan cannot see those, which is why the bug survived.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")

# Pages that render links at runtime. The corpus tree and the workbench detail
# page are the two that build anchors in JS.
RENDERED_PAGES = ["/index.html", "/workbench/detail.html"]

# Every page a fragment might point at.
TARGET_PAGES = [
    "/index.html",
    "/explorer/",
    "/workbench/detail.html",
    "/workbench/files.html",
    "/workbench/terminal.html",
    "/boardroom/",
]


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def _ids(page, url):
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(300)
    return set(page.evaluate("[...document.querySelectorAll('[id]')].map(e => e.id)"))


def _links(page, url):
    """Same-origin hrefs with a fragment, after the page's JS has run."""
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(400)
    return page.evaluate("""() => [...document.querySelectorAll('a[href]')]
        .map(a => a.getAttribute('href'))
        .filter(h => h && h.includes('#'))""")


@pytest.mark.parametrize("page_url", RENDERED_PAGES)
def test_every_rendered_fragment_link_resolves(server, session, page_url):
    """Each `path#fragment` link on a rendered page must find its anchor on
    the target page. This is the check that would have caught #310's bug
    directly, instead of via a hand-written assertion about one known
    anchor."""
    page = session.new_page()
    hrefs = _links(page, server.url + page_url)

    targets = {}
    unresolved = []
    for href in hrefs:
        path, _, fragment = href.partition("#")
        if not fragment:
            continue
        # Resolve the target page, defaulting to this page for a bare `#id`.
        if path.startswith(("http://", "https://", "//")):
            continue
        target = path or page_url
        if target.startswith("./"):
            target = target[2:]
        url = server.url + (target if target.startswith("/") else "/" + target)
        if url not in targets:
            targets[url] = _ids(page, url)
        if fragment not in targets[url]:
            unresolved.append(f"{href} -> no #{fragment} on {target}")

    page.close()
    assert hrefs, f"{page_url} rendered no fragment links — did the page break?"
    assert not unresolved, (
        f"fragment link(s) point at non-existent anchors on {page_url}:\n  "
        + "\n  ".join(sorted(unresolved))
    )


def test_corpus_tree_deep_links_land_on_the_detail_page(server, session):
    """The specific contract from #310, asserted end to end: a corpus-tree row
    click must reveal real content, not just navigate near it."""
    page = session.new_page()
    hrefs = _links(page, server.url + "/index.html")
    detail = [h for h in hrefs if h.startswith("workbench/detail.html#")]
    assert detail, f"corpus tree has no detail deep links: {hrefs}"

    for href in detail:
        fragment = href.split("#", 1)[1]
        page.goto(server.url + "/" + href, wait_until="networkidle")
        page.wait_for_timeout(500)
        assert page.locator(f"[id='{fragment}']").count() == 1, (
            f"{href} did not land on an element"
        )
    page.close()


# --- slug() drift guard (issue #313, item 2) ---

def test_slug_implementations_agree():
    """`docs/index.html` and `docs/workbench/detail.html` each define a
    `slug()`; they must stay in step or deep links silently break. Both are
    extracted and run against the same inputs."""
    src_index = open(os.path.join(DOCS, "index.html"), encoding="utf-8").read()
    src_detail = open(os.path.join(DOCS, "workbench", "detail.html"),
                      encoding="utf-8").read()
    pat = re.compile(r"function slug\(s\)\s*\{([^}]*)\}")
    a, b = pat.search(src_index), pat.search(src_detail)
    assert a and b, "slug() missing from one of the pages"
    assert a.group(1).strip() == b.group(1).strip(), (
        "the two slug() implementations have diverged — deep links will break\n"
        f"  index.html:  {a.group(1).strip()}\n"
        f"  detail.html: {b.group(1).strip()}"
    )


def test_slug_is_reachable_by_css_selector(server, session):
    """The reason slug() exists: a dotted work id (`bwv227.1`) in an `id`
    cannot be reached by a plain CSS selector. Every rendered anchor id must
    therefore be selector-safe."""
    page = session.new_page()
    for url in ("/index.html", "/workbench/detail.html"):
        page.goto(server.url + url, wait_until="networkidle")
        page.wait_for_timeout(400)
        ids = page.evaluate("""() => [...document.querySelectorAll('a[href*="#"]')]
            .map(a => a.getAttribute('href').split('#')[1]).filter(Boolean)""")
        for anchor in set(ids):
            assert re.fullmatch(r"[A-Za-z0-9_-]+", anchor), (
                f"{url}: anchor id {anchor!r} is not CSS-selector-safe"
            )
    page.close()


# --- jump links after an era re-render (issue #313, item 3) ---

def test_jump_link_still_opens_target_after_era_change(server, session):
    """The era filter replaces #works. The jump bar is rebuilt with it, so a
    click afterwards must still open its target (nav + count are pinned in
    #310; this pins the click behavior)."""
    page = session.new_page()
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    for era in ("classical", "romantic"):
        page.select_option("#era-select", era)
        page.wait_for_timeout(300)
        link = page.locator("#jump a[data-rev]").nth(1)
        target_id = link.get_attribute("data-rev")
        link.click()
        page.wait_for_timeout(200)
        assert page.locator(f"details.wb-rev#{target_id}").evaluate("el => el.open"), (
            f"jump link did not open {target_id} after era={era}"
        )
    page.close()


# --- spike listener (issue #313, item 4) ---

def test_spike_listener_page_mounts(server, session):
    """The spike listener is the standing quality gate (per
    docs/checkpoint-egg-model.md §5) but had no DOM test — only the link
    sweep reached it."""
    page = session.new_page()
    page.goto(server.url + "/spike/index.html", wait_until="networkidle")
    page.wait_for_timeout(300)
    body = page.inner_text("body").lower()
    assert body.strip(), "spike listener page rendered empty"
    assert page.locator("audio, a[href$='.wav'], ul li").count() > 0, (
        "spike listener lists no evidence artifacts"
    )
    page.close()