"""Tests for the doc-prose lint (T7, issue #299).

Two tiers:

  * **Behavioral** — each check is exercised against a synthetic repo in
    ``tmp_path`` so the test proves the check *catches* its drift class, and
    the false-positive guards are pinned (prose refs, historical mentions,
    superseded docs, archived records).
  * **Repo gate** — the real ``dev`` tree must lint clean. This is the
    regression gate: the moment drift lands, this fails.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_docs.lint import (  # noqa: E402
    is_historical, lint_backtick_path, lint_link, lint_repo, lint_stale_open_ref,
    repo_root, summarize, superseded_paths,
)

REPO = repo_root()


def make_repo(tmp_path, files):
    """Materialize {relpath: text} under tmp_path; return the root."""
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return str(tmp_path)


# --- broken-link ---

def test_broken_link_detected(tmp_path):
    root = make_repo(tmp_path, {"a/one.md": "see [x](missing.md)\n"})
    f = lint_link("a/one.md", "missing.md", root)
    assert f and f["kind"] == "broken-link"


def test_valid_link_ok(tmp_path):
    root = make_repo(tmp_path, {"a/one.md": "[x](two.md)\n", "a/two.md": "hi\n"})
    assert lint_link("a/one.md", "two.md", root) is None


def test_link_resolves_from_document_directory(tmp_path):
    """Depth matters: `../FORMAT_SPEC.md` from docs/ vs docs/design/."""
    root = make_repo(tmp_path, {"docs/FORMAT_SPEC.md": "x\n", "docs/design/d.md": ""})
    # one level up from docs/design/ -> docs/FORMAT_SPEC.md : resolves
    assert lint_link("docs/design/d.md", "../FORMAT_SPEC.md", root) is None
    # two levels up escapes the repo root : does not resolve
    assert lint_link("docs/design/d.md", "../../FORMAT_SPEC.md", root) is not None


def test_anchor_and_absolute_links_ignored(tmp_path):
    root = make_repo(tmp_path, {"a/one.md": ""})
    for target in ("#section", "https://example.com/x", "mailto:x@y.z"):
        assert lint_link("a/one.md", target, root) is None


# --- unresolved-ref ---

def test_unresolved_backtick_path_detected(tmp_path):
    root = make_repo(tmp_path, {"a/one.md": ""})
    f = lint_backtick_path("a/one.md", "tools/nope", root)
    assert f and f["kind"] == "unresolved-ref"


def test_existing_backtick_path_ok(tmp_path):
    root = make_repo(tmp_path, {"tools/real/keep.py": "", "a/one.md": ""})
    assert lint_backtick_path("a/one.md", "tools/real/keep.py", root) is None


def test_command_line_in_backticks_truncated_to_path(tmp_path):
    """`tools/muse_seed_cli/cli.py validate` — the trailing word is an
    argument, not part of the path (found in muse_workbench_runner)."""
    root = make_repo(tmp_path, {"tools/muse_seed_cli/cli.py": "", "a/one.md": ""})
    assert lint_backtick_path(
        "a/one.md", "tools/muse_seed_cli/cli.py validate", root) is None


def test_prose_refs_are_not_path_claims(tmp_path):
    """Placeholders, globs and abbreviated lists are prose, not claims."""
    root = make_repo(tmp_path, {"a/one.md": ""})
    for ref in (
        "docs/audit/YYYY-MM-DD-system-audit.md",
        "docs/spike/mockup-v1/v2/v3.json",
        "seeds/bwv227.1.v1/v2",
        "docs/design/e1..e3",
        "tests/**/test_*.py",
    ):
        assert lint_backtick_path("a/one.md", ref, root) is None, ref


def test_relative_backtick_ref_allowed(tmp_path):
    """A path written relative to the doc still counts as resolving."""
    root = make_repo(tmp_path, {"docs/audio/README.md": "", "docs/design/d.md": ""})
    assert lint_backtick_path("docs/design/d.md", "audio/README.md", root) is None


# --- stale-open-ref ---

def test_stale_open_ref_detected(tmp_path):
    root = make_repo(tmp_path, {"tests/closed_2026_x.md": "", "a/one.md": ""})
    f = lint_stale_open_ref("a/one.md", "tests/open_2026_x.md", root)
    assert f and f["kind"] == "stale-open-ref"
    assert "closed_2026_x.md" in f["detail"]


def test_live_open_ref_ok(tmp_path):
    root = make_repo(tmp_path, {"tests/open_2026_x.md": "", "a/one.md": ""})
    assert lint_stale_open_ref("a/one.md", "tests/open_2026_x.md", root) is None


# --- exclusions that keep the signal honest ---

@pytest.mark.parametrize("rel", [
    "tests/closed_2026_x.md",
    "bugs/open_2026_y.md",
    "blockers/closed_2026_z.md",
    "docs/audit/2026-08-26-system-audit-a1-2.md",
])
def test_historical_records_excluded(rel):
    """Records describe past state; moved paths are not drift in a record."""
    assert is_historical(rel)


@pytest.mark.parametrize("rel", ["docs/pipeline.md", "AGENTS.md", "tools/x/README.md"])
def test_live_docs_not_excluded(rel):
    assert not is_historical(rel)


def test_superseded_listing_excludes_schema_spec(tmp_path):
    root = make_repo(tmp_path, {
        "docs/superseded.txt": "# comment\nSCHEMA_SPEC.md\n\n",
        "SCHEMA_SPEC.md": "dead `docs/gone.md` link and [x](nope.md)\n",
    })
    assert os.path.normpath("SCHEMA_SPEC.md") in superseded_paths(root)
    assert lint_repo(root) == []


def test_historical_mention_skipped(tmp_path):
    """Prose about a removed path is not drift: 'not the earlier `X`'."""
    root = make_repo(tmp_path, {
        "docs/design/d.md": (
            "The loader uses the current IR, not the earlier `tools/muse_ir/`: "
            "written-event counts differ.\n"
        ),
    })
    assert lint_repo(root) == []


def test_unqualified_dead_path_in_doc_still_flagged(tmp_path):
    """A dead path with no historical framing *is* drift."""
    root = make_repo(tmp_path, {"docs/design/d.md": "Load `tools/muse_ir/` first.\n"})
    assert any(f["kind"] == "unresolved-ref" for f in lint_repo(root))


def test_findings_deduplicated_per_file(tmp_path):
    """The same reference three times is one finding, not three."""
    root = make_repo(tmp_path, {
        "a/one.md": "[x](gone.md)\n[y](gone.md)\n[z](gone.md)\n",
    })
    assert len(lint_repo(root)) == 1


def test_encoding_finding_not_a_crash(tmp_path):
    """A non-UTF-8 doc is reported, not raised (found live in r1-)."""
    path = tmp_path / "docs" / "bad.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"ok \xd1 bad\n")
    findings = lint_repo(str(tmp_path))
    assert any(f["kind"] == "encoding" for f in findings)


def test_unfilled_template_detected(tmp_path):
    root = make_repo(tmp_path, {"docs/design/d.md": "Text\n\n[TODO] fill this\n"})
    assert any(f["kind"] == "unfilled-template" for f in lint_repo(root))


def test_backticked_marker_is_documentation_not_a_finding(tmp_path):
    """``flags `[TODO]`s`` talks *about* the marker; it is not an unfilled
    template (found live: this tool's own AGENTS.md convention line)."""
    root = make_repo(tmp_path, {
        "AGENTS.md": "Run the lint — it flags unfilled `[TODO]`s and TBDs.\n",
    })
    assert lint_repo(root) == []


def test_own_tool_docs_are_exempt(tmp_path):
    """muse_docs' own README quotes the markers by design."""
    root = make_repo(tmp_path, {
        "tools/muse_docs/README.md": "flags `[TODO]` and `tools/nope`\n",
        "tools/muse_docs/lint.py": "",
    })
    assert lint_repo(root) == []


# --- repo gate ---

def test_real_repo_has_no_findings():
    """The regression gate: `dev` must lint clean. If this fails, the
    message lists exactly what to fix."""
    findings = lint_repo(REPO)
    detail = "\n".join(
        "%s: [%s] %s — %s" % (f["file"], f["kind"], f["ref"], f["detail"])
        for f in findings
    )
    assert findings == [], "doc-prose drift found:\n%s" % detail


def test_repo_scan_is_deterministic():
    """Same tree, same output — the lint must not be order-dependent."""
    assert lint_repo(REPO) == lint_repo(REPO)


def test_summarize_shape():
    findings = [
        {"kind": "broken-link"},
        {"kind": "broken-link"},
        {"kind": "encoding"},
    ]
    assert summarize(findings) == {"broken-link": 2, "encoding": 1}