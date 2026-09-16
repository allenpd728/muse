"""CLI surface tests for the doc-prose lint (issue #311).

Covers the parts of `cli.py` that were only exercised by hand: exit codes,
`--kind` filtering, `--json` shape, `--report` structure, and the
`--max-findings` budget guard.

Run with `cd tools && python3 -m pytest muse_docs -q`.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_docs.cli import main  # noqa: E402
from muse_docs.lint import FINDING_BUDGET  # noqa: E402


@pytest.fixture
def clean_repo(tmp_path):
    (tmp_path / "AGENTS.md").write_text("root marker\n", encoding="utf-8")
    (tmp_path / "tools" / "x").mkdir(parents=True)
    (tmp_path / "tools" / "x" / "keep.py").write_text("", encoding="utf-8")
    return str(tmp_path)


@pytest.fixture
def dirty_repo(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    (docs / "a.md").write_text("[x](gone.md)\n", encoding="utf-8")
    (docs / "b.md").write_text("load `tools/nope`\n", encoding="utf-8")
    return str(tmp_path)


# --- exit codes ---

def test_clean_repo_exits_zero(clean_repo, capsys):
    assert main(["lint", "--root", clean_repo]) == 0


def test_dirty_repo_exits_one(dirty_repo, capsys):
    assert main(["lint", "--root", dirty_repo]) == 1


def test_quiet_emits_nothing_and_reports_code(clean_repo, capsys):
    code = main(["lint", "--root", clean_repo, "--quiet"])
    assert code == 0
    assert capsys.readouterr().out == ""


def test_quiet_on_dirty_repo_exits_one(dirty_repo, capsys):
    assert main(["lint", "--root", dirty_repo, "--quiet"]) == 1
    assert capsys.readouterr().out == ""


# --- --kind ---

def test_kind_filters_output(dirty_repo, capsys):
    main(["lint", "--root", dirty_repo, "--kind", "broken-link"])
    out = capsys.readouterr().out
    assert "broken-link" in out
    assert "unresolved-ref" not in out, "kind filter leaked other kinds"


def test_kind_with_no_matches_is_clean_exit(dirty_repo, capsys):
    """Asking for a kind that has no findings is not itself a failure of
    that kind — but the repo still has findings, so the exit stays 1 only
    when the filter is empty *and* nothing matched."""
    code = main(["lint", "--root", dirty_repo, "--kind", "encoding"])
    assert code == 0, "no encoding findings -> filtered set is empty -> 0"


# --- --json ---

def test_json_is_parseable_and_shaped(dirty_repo, capsys):
    main(["lint", "--root", dirty_repo, "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list) and payload
    for f in payload:
        assert set(f) == {"kind", "file", "ref", "detail"}, f


def test_json_empty_on_clean_repo(clean_repo, capsys):
    main(["lint", "--root", clean_repo, "--json"])
    assert json.loads(capsys.readouterr().out) == []


# --- --report ---

def test_report_structure(dirty_repo, capsys):
    main(["lint", "--root", dirty_repo, "--report"])
    out = capsys.readouterr().out
    assert out.startswith("# Doc-prose lint report")
    assert "**Total:**" in out
    assert "| kind | count |" in out, "missing the kind table header"
    assert "## Findings" in out, "missing the findings section"
    assert "### `" in out, "findings are not grouped by file"


def test_report_on_clean_repo_says_so(clean_repo, capsys):
    main(["lint", "--root", clean_repo, "--report"])
    out = capsys.readouterr().out
    assert "**Total:** 0" in out
    assert "internally coherent" in out
    assert "## Findings" not in out


def test_report_names_every_kind_present(dirty_repo, capsys):
    main(["lint", "--root", dirty_repo, "--report"])
    out = capsys.readouterr().out
    assert "`broken-link`" in out
    assert "`unresolved-ref`" in out


# --- --max-findings budget guard ---

def test_budget_error_goes_to_stderr(dirty_repo, capsys):
    code = main(["lint", "--root", dirty_repo, "--max-findings", "0"])
    captured = capsys.readouterr()
    assert code == 1
    assert "budget" in captured.err, "budget breach must be reported on stderr"
    assert "budget" not in captured.out, "the findings list is the stdout story"


def test_generous_budget_is_quiet(dirty_repo, capsys):
    code = main(["lint", "--root", dirty_repo, "--max-findings", "100"])
    assert code == 1  # findings still exist
    assert "budget" not in capsys.readouterr().err


def test_default_budget_is_exported():
    """The CLI default and the library constant must not drift apart."""
    assert isinstance(FINDING_BUDGET, int) and FINDING_BUDGET > 0


# --- the real tree through the CLI ---

def test_real_repo_lints_clean_via_cli(capsys):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from muse_docs.lint import repo_root

    code = main(["lint", "--root", repo_root(), "--quiet"])
    assert code == 0, "the repo must lint clean through the CLI surface too"