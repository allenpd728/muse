"""Tests for the opt-in status-claim check (T7b, issue #315).

Two tiers, matching the rest of the suite:

  * **Behavioral** — parsing and comparison are exercised against synthetic
    docs and cache fixtures in ``tmp_path``, so the test proves the check
    catches stale claims and, equally, that it stays quiet when it should.
  * **Offline guard** — ``--check-issues`` must never touch the network, and
    must not run unless the flag is passed. The former is proven by making
    any network call raise, the latter by asserting the default path.

Run with `cd tools && python3 -m pytest muse_docs -q`.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_docs import cli  # noqa: E402
from muse_docs import issue_claims  # noqa: E402

REPO = issue_claims.DEFAULT_REPO


def write_cache(path, issues):
    path.write_text(
        json.dumps({"repo": REPO, "refreshed_at": "2026-09-22T00:00:00Z",
                    "issues": {str(k): v for k, v in issues.items()}}),
        encoding="utf-8",
    )
    return str(path)


def make_repo(tmp_path, files):
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return str(tmp_path)


# --- parsing: what counts as a claim ---

def test_bold_done_claim_parsed():
    text = "| W1 — IR | what | **done** (#123 + #128 → [x](y)) |\n"
    claims = issue_claims.parse_status_claims(text, "docs/pipeline.md")
    assert {c["ref"] for c in claims} == {"#123", "#128"}
    assert all(c["claim"] == "done" for c in claims)


def test_bare_done_claim_parsed():
    text = "| W2 | what | **done (#125)** |\n"
    claims = issue_claims.parse_status_claims(text, "docs/pipeline.md")
    assert [c["ref"] for c in claims] == ["#125"]


def test_cell_leading_done_parsed():
    text = "| W6 | what | Profiled the blocker | done (#317) |\n"
    claims = issue_claims.parse_status_claims(text, "docs/pipeline.md")
    assert [c["ref"] for c in claims] == ["#317"]


def test_decomposed_claim_is_not_a_done_claim():
    """`**decomposed #139 ... all done**` is not "issue #139 is closed"."""
    text = ("| S3 — Seed | what | **decomposed #139 → S3.1–S3.6 (#142–#147), "
            "all done** |\n")
    claims = issue_claims.parse_status_claims(text, "docs/pipeline.md")
    assert claims == []


def test_filed_claim_is_not_a_done_claim():
    text = "| S5 | what | **done (#141)**; S5.1 filed [#249](https://x/249) |\n"
    claims = issue_claims.parse_status_claims(text, "docs/pipeline.md")
    assert [c["ref"] for c in claims] == ["#141"]


def test_prose_status_word_is_not_a_claim():
    """`status:done` labels describe the vocabulary, not an issue's state."""
    text = "The `status:done` label means work landed on main.\n"
    assert issue_claims.parse_status_claims(text, "docs/x.md") == []


def test_duplicate_number_in_one_cell_is_one_claim():
    text = "| A | b | **done** (#12, see also #12) |\n"
    claims = issue_claims.parse_status_claims(text, "docs/x.md")
    assert len(claims) == 1


# --- comparison: stale vs clean vs unknown ---

def test_open_issue_contradicts_done_claim():
    findings = issue_claims.check_status_claims(
        [{"file": "docs/pipeline.md", "line": 3, "ref": "#9", "claim": "done"}],
        {"9": "open"},
    )
    assert len(findings) == 1
    assert findings[0]["kind"] == "stale-status"
    assert "#9" in findings[0]["ref"]


def test_closed_issue_satisfies_done_claim():
    assert issue_claims.check_status_claims(
        [{"file": "docs/pipeline.md", "line": 3, "ref": "#9", "claim": "done"}],
        {"9": "closed"},
    ) == []


def test_unknown_issue_is_skipped_not_flagged():
    """Absent from the cache means unknown — never a false positive."""
    assert issue_claims.check_status_claims(
        [{"file": "docs/pipeline.md", "line": 3, "ref": "#9", "claim": "done"}],
        {},
    ) == []


# --- cache loading ---

def test_missing_cache_returns_error(tmp_path):
    issues, err = issue_claims.load_cache(str(tmp_path / "nope.json"))
    assert issues == {} and "no issue cache" in err


def test_unreadable_cache_returns_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    issues, err = issue_claims.load_cache(str(bad))
    assert issues == {} and "unreadable" in err


def test_cache_roundtrip(tmp_path):
    p = tmp_path / "cache.json"
    write_cache(p, {1: "closed", 2: "open"})
    issues, err = issue_claims.load_cache(str(p))
    assert err is None
    assert issues == {"1": "closed", "2": "open"}


# --- CLI surface ---

def test_check_issues_flags_stale_claim(tmp_path, capsys):
    root = make_repo(tmp_path, {
        "AGENTS.md": "root\n",
        "tools/x/keep.py": "",
        "docs/pipeline.md": "| W1 | what | **done (#9)** |\n",
    })
    cache = write_cache(tmp_path / "cache.json", {9: "open"})
    code = cli.main(["lint", "--root", root, "--check-issues",
                     "--issue-cache", cache, "--kind", "stale-status"])
    out = capsys.readouterr().out
    assert code == 1
    assert "stale-status" in out and "#9" in out


def test_check_issues_quiet_when_claim_fresh(tmp_path, capsys):
    root = make_repo(tmp_path, {
        "AGENTS.md": "root\n",
        "tools/x/keep.py": "",
        "docs/pipeline.md": "| W1 | what | **done (#9)** |\n",
    })
    cache = write_cache(tmp_path / "cache.json", {9: "closed"})
    code = cli.main(["lint", "--root", root, "--check-issues",
                     "--issue-cache", cache], )
    assert code == 0
    assert capsys.readouterr().out.count("finding") == 1


def test_missing_cache_warns_and_does_not_flag(tmp_path, capsys):
    root = make_repo(tmp_path, {
        "AGENTS.md": "root\n",
        "tools/x/keep.py": "",
        "docs/pipeline.md": "| W1 | what | **done (#9)** |\n",
    })
    code = cli.main(["lint", "--root", root, "--check-issues",
                     "--issue-cache", str(tmp_path / "absent.json")])
    captured = capsys.readouterr()
    assert code == 0  # a missing cache is a warning, not a finding
    assert "WARNING" in captured.err and "no issue cache" in captured.err


def test_quiet_preserves_exit_codes_with_check_issues(tmp_path):
    root = make_repo(tmp_path, {
        "AGENTS.md": "root\n",
        "tools/x/keep.py": "",
        "docs/pipeline.md": "| W1 | what | **done (#9)** |\n",
    })
    cache = write_cache(tmp_path / "cache.json", {9: "open"})
    assert cli.main(["lint", "--root", root, "--check-issues",
                     "--issue-cache", cache, "--quiet"]) == 1
    cache2 = write_cache(tmp_path / "cache2.json", {9: "closed"})
    assert cli.main(["lint", "--root", root, "--check-issues",
                     "--issue-cache", cache2, "--quiet"]) == 0


def test_no_flag_means_no_check(tmp_path, capsys):
    """Without `--check-issues` the cache is never read — no claim check."""
    root = make_repo(tmp_path, {
        "AGENTS.md": "root\n",
        "tools/x/keep.py": "",
        "docs/pipeline.md": "| W1 | what | **done (#9)** |\n",
    })
    cache = write_cache(tmp_path / "cache.json", {9: "open"})
    # Point the default cache at a stale one; without the flag it is ignored.
    code = cli.main(["lint", "--root", root, "--issue-cache", cache])
    assert code == 0


# --- the network guard ---

def test_check_issues_makes_no_network_call(tmp_path, monkeypatch):
    """`--check-issues` must be offline: any network call is a test failure."""
    root = make_repo(tmp_path, {
        "AGENTS.md": "root\n",
        "tools/x/keep.py": "",
        "docs/pipeline.md": "| W1 | what | **done (#9)** |\n",
    })
    cache = write_cache(tmp_path / "cache.json", {9: "open"})

    def boom(*a, **k):
        raise AssertionError("network call during offline check")

    monkeypatch.setattr(issue_claims.urllib.request, "urlopen", boom)
    code = cli.main(["lint", "--root", root, "--check-issues",
                     "--issue-cache", cache, "--quiet"])
    assert code == 1  # the finding still surfaced, offline


def test_fast_suite_does_not_invoke_network(monkeypatch, tmp_path):
    """The default lint path must never call the refresh routine."""
    root = make_repo(tmp_path, {
        "AGENTS.md": "root\n",
        "tools/x/keep.py": "",
        "docs/pipeline.md": "| W1 | what | **done (#9)** |\n",
    })

    def boom(*a, **k):
        raise AssertionError("refresh_cache called by the default lint path")

    monkeypatch.setattr(issue_claims, "refresh_cache", boom)
    monkeypatch.setattr(cli, "refresh_cache", boom)
    assert cli.main(["lint", "--root", root, "--quiet"]) == 0


def test_real_repo_lints_clean_without_flag():
    """The repo gate is unchanged: no `--check-issues`, still clean."""
    from muse_docs.lint import repo_root
    assert cli.main(["lint", "--root", repo_root(), "--quiet"]) == 0
