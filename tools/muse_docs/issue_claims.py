"""Opt-in status-claim check for the doc-prose lint (issue #315, T7b).

The offline lint (`lint.py`) deliberately stops at mechanically decidable
*local* facts — links, paths, renames. This module adds the one check that
needs the issue queue: whether a doc's status claims about issue numbers
match the live queue.

The no-spend constraint is preserved by splitting the network out:

  * ``parse_status_claims()`` — offline. Reads a doc, returns the claims it
    makes about issue numbers.
  * ``refresh_cache()`` — the **only** function here that touches the
    network. Run explicitly, by hand, never from CI or the test suite.
  * ``check_status_claims()`` — offline. Compares claims against a cached
    snapshot of issue states.

So ``lint --check-issues`` reads a local JSON cache and makes zero network
calls; ``refresh-issues`` is the documented way to populate that cache.

What counts as a claim, and its expected state:

  * a ``done``-claim — a bold ``**done`` run, or a table status cell that
    begins ``done``, followed by one or more ``#N`` issue references:
    expected state **closed**. An open issue here is drift.
  * ``filed``-claims (``... filed [#N]``) are **not** reportable: filing an
    issue and later closing it is the normal lifecycle, so "filed" is a
    timestamp, not a state assertion. Recorded in ``docs/decision-log.md``.
  * bare ``status:done`` / ``status:available`` label *strings* describe the
    label vocabulary (TASK_WORKFLOW.md), not a specific issue's state, so
    they are not claims. Also recorded in the decision log.

The check is conservative: a claim whose issue is absent from the cache is
skipped rather than flagged, because the only honest statement is "unknown",
and a false positive here fails the queue for no reason.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

DEFAULT_CACHE = os.path.join("tools", "muse_docs", "issue_cache.json")
DEFAULT_REPO = "philipdallen/rubato"

# A "done" marker: a bold run starting with `done`, or the start of a table
# status cell beginning with `done`. Requiring the marker to lead keeps
# `**decomposed #139 ... all done**` (a different claim — that sub-tasks were
# decomposed) from being read as "issue #139 is closed".
BOLD_DONE_RE = re.compile(r"\*\*done\b")
CELL_DONE_RE = re.compile(r"^\s*done\b")

# Stop scanning for issue numbers at a claim terminator: another clause, a
# separate filed-reference, or a table cell boundary.
_TERMINATORS = (";", "|", "\n")
# `filed`/`open` inside the same clause starts a *different* claim.
_OTHER_CLAIM_RE = re.compile(r"\bfiled\b|\bopen\b")

ISSUE_NUM_RE = re.compile(r"#(\d+)")


def _iter_table_cells(line):
    """Yield (cell_text, start_offset) for a markdown table row."""
    if not line.startswith("|"):
        return
    offset = 0
    for part in line.split("|"):
        yield part, offset
        offset += len(part) + 1


def _numbers_after(text, start):
    """Issue numbers claimed from ``start`` to the next terminator."""
    window = text[start:]
    cut = len(window)
    for term in _TERMINATORS:
        idx = window.find(term)
        if idx != -1:
            cut = min(cut, idx)
    # A `filed`/`open` marker in the same clause begins another claim.
    other = _OTHER_CLAIM_RE.search(window)
    if other and other.start() < cut:
        cut = other.start()
    return [int(n) for n in ISSUE_NUM_RE.findall(window[:cut])]


def parse_status_claims(text, relpath):
    """Every ``done``-claim a document makes about issue numbers.

    Returns a list of ``{file, line, ref, claim}`` dicts, de-duplicated per
    (file, line, ref) so a number repeated in one cell is one claim.
    """
    out = []
    seen = set()
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        for cell, offset in _iter_table_cells(line):
            m = BOLD_DONE_RE.search(cell) or CELL_DONE_RE.search(cell)
            if not m:
                continue
            for num in _numbers_after(cell, m.end()):
                key = (relpath, lineno, num)
                if key in seen:
                    continue
                seen.add(key)
                out.append({
                    "file": relpath,
                    "line": lineno,
                    "ref": "#%d" % num,
                    "claim": "done",
                })
    return out


def load_cache(path):
    """Load the issue-state cache. Returns (issues, error_or_None)."""
    if not os.path.isfile(path):
        return {}, "no issue cache at %s — run `refresh-issues` first" % path
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        return {}, "unreadable issue cache at %s: %s" % (path, exc)
    issues = data.get("issues") if isinstance(data, dict) else None
    if not isinstance(issues, dict):
        return {}, "issue cache at %s has no `issues` map" % path
    return {str(k): str(v) for k, v in issues.items()}, None


def check_status_claims(claims, issues):
    """Findings for claims whose cached state contradicts the claim.

    A ``done``-claim expects ``closed``. Only an explicit ``open`` in the
    cache contradicts it; an issue absent from the cache is unknown and is
    skipped (see module docstring).
    """
    findings = []
    for c in claims:
        num = c["ref"].lstrip("#")
        state = issues.get(num)
        if state != "open":
            continue
        findings.append({
            "kind": "stale-status",
            "file": c["file"],
            "ref": "%s (%s, line %d)" % (c["ref"], c["claim"], c["line"]),
            "detail": "claim `%s` but the issue is still open" % c["claim"],
        })
    return findings


def _api_get(url, token, timeout=20):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "muse-docs-status-check",
    })
    if token:
        req.add_header("Authorization", "Bearer %s" % token)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def refresh_cache(cache_path, repo=DEFAULT_REPO, token=None, numbers=None):
    """Populate the cache from the GitHub API. **Network. Explicit only.**

    ``numbers`` restricts the fetch; when omitted every issue (open + closed)
    is pulled. Returns (count, error_or_None).
    """
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    states = {}
    try:
        page = 1
        while True:
            url = ("https://api.github.com/repos/%s/issues"
                   "?state=all&per_page=100&page=%d" % (repo, page))
            batch = _api_get(url, token)
            if not batch:
                break
            for item in batch:
                num = str(item.get("number"))
                states[num] = item.get("state", "unknown")
            if len(batch) < 100:
                break
            page += 1
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return 0, "refresh failed: %s" % exc

    if numbers is not None:
        keep = {str(n) for n in numbers}
        states = {k: v for k, v in states.items() if k in keep}

    payload = {
        "repo": repo,
        "refreshed_at": _utcnow(),
        "issues": states,
    }
    os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return len(states), None


def _utcnow():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
