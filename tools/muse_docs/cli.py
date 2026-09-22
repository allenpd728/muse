"""muse-docs CLI: mechanical doc-prose lint (T7, issue #299).

    python3 tools/muse_docs/cli.py lint              # findings; exit 1 if any
    python3 tools/muse_docs/cli.py lint --report     # triage report (markdown)
    python3 tools/muse_docs/cli.py lint --kind broken-link
    python3 tools/muse_docs/cli.py lint --json

Deterministic and offline: no network, no model. The agent's own session is
the prose layer (AGENTS.md checklist convention); this is the cheap
mechanical tier that runs in the fast test suite.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_docs.lint import (  # noqa: E402
    FINDING_BUDGET, check_budget, format_findings, iter_markdown, lint_repo,
    read_text_checked, repo_root, summarize,
)
from muse_docs.issue_claims import (  # noqa: E402
    DEFAULT_CACHE, DEFAULT_REPO, check_status_claims, load_cache,
    parse_status_claims, refresh_cache,
)

KIND_HELP = {
    "broken-link": "a relative markdown link whose target does not exist",
    "unresolved-ref": "a backticked live-repo path that does not resolve",
    "stale-open-ref": "an open_* record that has since been renamed closed_",
    "unfilled-template": "a raw [TODO]/TBD placeholder left in a doc",
    "encoding": "a markdown file that is not valid UTF-8",
    "stale-status": "a doc says an issue is done but the queue has it open",
}


def _report(findings, root):
    """Markdown triage report — the shape that belongs in docs/audit/."""
    counts = summarize(findings)
    lines = [
        "# Doc-prose lint report",
        "",
        "Mechanical findings from `tools/muse_docs` (T7, #299). Offline and",
        "deterministic. Triage these into `documentation` issues; the queue is",
        "non-blocking but the suite fails while any exist.",
        "",
        "**Total:** %d" % len(findings),
        "",
        "| kind | count | what it catches |",
        "|---|---|---|",
    ]
    for kind, n in counts.items():
        lines.append("| `%s` | %d | %s |" % (kind, n, KIND_HELP.get(kind, "")))
    lines.append("")
    if findings:
        lines.append("## Findings")
        lines.append("")
        current = None
        for f in findings:
            if f["file"] != current:
                current = f["file"]
                lines.append("### `%s`" % current)
                lines.append("")
            lines.append("- `%s` — %s" % (f["ref"], f["detail"]))
            lines.append("")
    else:
        lines.append("No findings. The docs are internally coherent.")
    return "\n".join(lines)


def _check_issue_claims(root, cache_path, warnings):
    """Offline status-claim findings, or ``None`` when the cache is missing.

    Reads a local cache only — the network lives in ``refresh-issues``, so
    ``lint --check-issues`` stays offline (the tool's whole premise).
    """
    issues, err = load_cache(cache_path)
    if err:
        # Offline: report the missing cache as a warning, not a finding.
        warnings.append(err)
        return None
    claims = []
    for relpath, path in iter_markdown(root):
        text, _ = read_text_checked(path)
        claims.extend(parse_status_claims(text, relpath))
    return check_status_claims(claims, issues)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-docs", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lint", help="run the mechanical doc lint")
    p.add_argument("--root", default=None, help="repo root (default: auto)")
    p.add_argument("--report", action="store_true",
                   help="emit a markdown triage report instead of a list")
    p.add_argument("--json", action="store_true", help="emit findings as JSON")
    p.add_argument("--kind", default=None,
                   help="only findings of this kind (see README)")
    p.add_argument("--quiet", action="store_true", help="no output; exit code only")
    p.add_argument("--check-issues", action="store_true",
                   help="also compare doc status claims against a local issue "
                        "cache (offline; populate it with `refresh-issues`)")
    p.add_argument("--issue-cache", default=None,
                   help="path to the issue-state cache "
                        "(default: tools/muse_docs/issue_cache.json)")
    p.add_argument("--max-findings", type=int, default=FINDING_BUDGET,
                   help="fail loudly above this many findings (default %d); "
                        "guards against a mis-firing rule flooding the queue "
                        "rather than reporting real drift" % FINDING_BUDGET)

    r = sub.add_parser(
        "refresh-issues",
        help="populate the issue-state cache from GitHub (network; explicit only)")
    r.add_argument("--root", default=None, help="repo root (default: auto)")
    r.add_argument("--issue-cache", default=None, help="cache path to write")
    r.add_argument("--repo", default=DEFAULT_REPO, help="owner/name to query")

    args = ap.parse_args(argv)

    root = os.path.abspath(args.root or repo_root())

    if args.cmd == "refresh-issues":
        cache = args.issue_cache or os.path.join(root, DEFAULT_CACHE)
        count, err = refresh_cache(cache, repo=args.repo)
        if err:
            print("ERROR: " + err, file=sys.stderr)
            return 1
        print("wrote %d issue states to %s" % (count, cache))
        return 0

    findings = lint_repo(args.root)
    warnings = []
    if args.check_issues:
        cache = args.issue_cache or os.path.join(root, DEFAULT_CACHE)
        extra = _check_issue_claims(root, cache, warnings)
        if extra is not None:
            findings.extend(extra)
            findings.sort(key=lambda f: (f["file"], f["kind"], f["ref"]))

    budget_error = check_budget(findings, args.max_findings)
    if args.kind:
        findings = [f for f in findings if f["kind"] == args.kind]

    if args.quiet:
        return 1 if findings else 0

    for w in warnings:
        # The check was requested but could not run — say so on stderr, since
        # a silently skipped check is indistinguishable from a passing one.
        print("WARNING: " + w, file=sys.stderr)

    if budget_error:
        # Printed before the findings: a flood is the headline, not the list.
        print("ERROR: " + budget_error, file=sys.stderr)

    if args.json:
        print(json.dumps(findings, indent=2))
    elif args.report:
        print(_report(findings, args.root))
    else:
        print("doc-prose lint — %d finding(s)%s" % (
            len(findings),
            "" if not findings else " (%s)" % ", ".join(
                "%s=%d" % kv for kv in summarize(findings).items()),
        ))
        if findings:
            print()
            print(format_findings(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())