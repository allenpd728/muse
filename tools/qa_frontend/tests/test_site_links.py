"""Site-wide link integrity + nav follow-ups (issue #310).

The `workbench/terminal/` 404 fixed in #304 went unnoticed because nothing
asserted that the site's own links resolve. The sweep here is the general
form of that check: every same-origin href on every served page must resolve.

Two exemptions, both deliberate and documented so they cannot hide drift:

  * ``/audio/*.wav``  — rendered audio is session-local by convention
    (gitignored, regenerated on demand; docs/audio/README.md). Absent files
    are the expected state, not drift.
  * external schemes (`http:`, `mailto:`, `javascript:`, `#`) — not this
    site's problem to resolve.
"""

import glob
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")

HREF_RE = re.compile(r'href=["\']([^"\']+)["\']')
EXTERNAL = ("http://", "https://", "mailto:", "javascript:", "//", "#")


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def _html_files():
    return sorted(glob.glob(os.path.join(DOCS, "**", "*.html"), recursive=True))


def _resolve(page_path, href):
    """Map an href on `page_path` to a filesystem path (or None if exempt)."""
    if href.startswith(EXTERNAL):
        return None
    # A template literal (`href="${anchor}"`) is built at runtime; a static
    # scan cannot evaluate it. Those links are covered by the DOM-level tests
    # (test_corpus_tree_dom) instead.
    if "${" in href or "{{" in href:
        return None
    target = href.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return None
    if target.startswith("/"):
        return os.path.join(DOCS, target.lstrip("/"))
    return os.path.normpath(os.path.join(os.path.dirname(page_path), target))


def _is_session_audio(path):
    return path is not None and path.replace(os.sep, "/").endswith(".wav") \
        and "/audio/" in path.replace(os.sep, "/")


# --- The sweep (issue #310, item 3) ---

def test_every_same_origin_href_resolves():
    """Every internal link on every page points at something that exists.

    This is the general form of the #304 `terminal/` 404. Source-level (no
    browser) so it covers pages the DOM tests never open.
    """
    broken = []
    checked = 0
    for path in _html_files():
        rel = os.path.relpath(path, DOCS)
        text = open(path, encoding="utf-8", errors="replace").read()
        for m in HREF_RE.finditer(text):
            target = _resolve(path, m.group(1))
            if target is None or _is_session_audio(target):
                continue
            checked += 1
            if not os.path.exists(target):
                broken.append(f"{rel}: {m.group(1)}")
    assert checked > 40, f"sweep found only {checked} internal links — did the scan break?"
    assert not broken, "broken internal link(s):\n  " + "\n  ".join(sorted(broken))


def test_every_same_origin_href_serves_200(server):
    """The same contract over HTTP — a link can exist but not be servable
    (e.g. a directory without an index)."""
    broken = []
    for path in _html_files():
        rel = os.path.relpath(path, DOCS)
        text = open(path, encoding="utf-8", errors="replace").read()
        for m in HREF_RE.finditer(text):
            href = m.group(1)
            if href.startswith(EXTERNAL) or "${" in href or "{{" in href:
                continue
            path_only = href.split("#", 1)[0].split("?", 1)[0]
            if not path_only or path_only.startswith(("mailto:", "javascript:")):
                continue
            fs = _resolve(path, href)
            if _is_session_audio(fs):
                continue  # session-local by convention
            if path_only.startswith("/"):
                url = server.url + path_only
            else:
                url = server.url + "/" + os.path.relpath(
                    os.path.normpath(os.path.join(os.path.dirname(path), path_only)),
                    DOCS)
            try:
                with urllib.request.urlopen(url) as r:
                    if r.status != 200:
                        broken.append(f"{rel}: {href} -> {r.status}")
            except urllib.error.HTTPError as e:
                broken.append(f"{rel}: {href} -> HTTP {e.code}")
    assert not broken, "unservable internal link(s):\n  " + "\n  ".join(sorted(broken))


def test_audio_wav_exemption_is_real():
    """Guard the exemption: at least one page links /audio/*.wav, and the
    convention doc that justifies skipping them still says so."""
    linked = False
    for path in _html_files():
        if ".wav" in open(path, encoding="utf-8", errors="replace").read():
            linked = True
    assert linked, "no .wav links found — the exemption may be masking drift now"

    audio_readme = os.path.join(DOCS, "audio", "README.md")
    text = open(audio_readme, encoding="utf-8").read().lower()
    assert "session" in text and "generated, not committed" in text, (
        "docs/audio/README.md no longer states the session-local convention "
        "the sweep exemption depends on"
    )


# --- #310 item 1: nav survives the era-filter re-render ---

def test_nav_survives_era_rerender(server, session):
    """The era filter re-renders #works. The nav and jump bar live outside
    it, so they must be untouched — a regression pin on that placement."""
    page = session.new_page()
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    before = page.locator("nav.site-nav").count()
    for era in ("classical", "romantic", "baroque"):
        page.select_option("#era-select", era)
        page.wait_for_timeout(250)
        assert page.locator("nav.site-nav").count() == before, f"nav lost at {era}"
        assert page.locator("#jump a[data-rev]").count() == 4, f"jump bar lost at {era}"


# --- #310 item 4: deep links ---

def test_deep_link_opens_and_scrolls_to_revision(server, session):
    """`#rev-<work>-v3` must open that revision and scroll to it. The rows
    render asynchronously, so the browser's own anchor scroll fires too early
    — the page applies the hash after render (found in #310)."""
    target = "rev-bwv227-1-v3"
    page = session.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{server.url}/workbench/detail.html#{target}", wait_until="networkidle")
    page.wait_for_timeout(600)
    assert page.locator(f"details.wb-rev#{target}").evaluate("el => el.open"), (
        "deep link did not open its revision"
    )
    # and it actually scrolled there (not still at the top)
    top = page.evaluate(
        f"Math.round(document.getElementById('{target}').getBoundingClientRect().top)"
    )
    assert -50 <= top <= 400, f"did not scroll to the target (top={top})"


def test_work_level_deep_link_opens(server, session):
    """`#work-bwv227-1` (what the corpus tree links to) opens that work."""
    page = session.new_page()
    page.goto(server.url + "/workbench/detail.html#work-bwv227-1", wait_until="networkidle")
    page.wait_for_timeout(600)
    el = page.locator("#work-bwv227-1")
    assert el.count() == 1, "work-level anchor missing"
    assert el.locator("details.wb-rev").first.evaluate("d => d.open"), (
        "work anchor did not reveal its first revision"
    )


# --- #310 item 2: boardroom content pages ---

BOARDROOM_PAGES = ["deck.html", "status.html", "competitive.html",
                   "appendix.html", "asks.html"]


@pytest.mark.parametrize("name", BOARDROOM_PAGES)
def test_boardroom_content_page_links_resolve(server, name):
    """Content pages keep their own chrome (B1 scaffold contract) but their
    cross-links must still resolve — the #304 404 lived here."""
    text = open(os.path.join(DOCS, "boardroom", name), encoding="utf-8").read()
    hrefs = [m.group(1) for m in HREF_RE.finditer(text)]
    assert hrefs, f"{name} has no links at all"
    for href in hrefs:
        target = _resolve(os.path.join(DOCS, "boardroom", name), href)
        if target is None or _is_session_audio(target):
            continue
        assert os.path.exists(target), f"{name}: {href} does not resolve"


# --- #310 item 5: files.html nav grid row ---

def test_files_nav_does_not_overlap_panes(server, session):
    """The nav is a grid row on files.html; it must sit above the tree and
    main panes rather than overlapping them."""
    for w, h in ((1280, 900), (375, 812)):
        page = session.new_page()
        page.set_viewport_size({"width": w, "height": h})
        page.goto(server.url + "/workbench/files.html", wait_until="networkidle")
        page.wait_for_timeout(300)
        geo = page.evaluate("""() => {
          const rect = s => { const e = document.querySelector(s);
            if (!e) return null; const b = e.getBoundingClientRect();
            return {top: b.top, bottom: b.bottom, left: b.left, right: b.right}; };
          return {nav: rect('nav.site-nav'), tree: rect('nav.tree'), main: rect('main')};
        }""")
        nav, tree, main = geo["nav"], geo["tree"], geo["main"]
        assert nav and tree and main, f"missing element at {w}px: {geo}"
        assert nav["bottom"] <= tree["top"] + 1, (
            f"nav overlaps the tree at {w}px: nav.bottom={nav['bottom']} "
            f"tree.top={tree['top']}"
        )
        assert nav["bottom"] <= main["top"] + 1, (
            f"nav overlaps main at {w}px: nav.bottom={nav['bottom']} "
            f"main.top={main['top']}"
        )
        page.close()