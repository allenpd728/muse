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
    FINDING_BUDGET, check_budget, format_findings, lint_repo, summarize,
)

KIND_HELP = {
    "broken-link": "a relative markdown link whose target does not exist",
    "unresolved-ref": "a backticked live-repo path that does not resolve",
    "stale-open-ref": "an open_* record that has since been renamed closed_",
    "unfilled-template": "a raw [TODO]/TBD placeholder left in a doc",
    "encoding": "a markdown file that is not valid UTF-8",
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
    p.add_argument("--max-findings", type=int, default=FINDING_BUDGET,
                   help="fail loudly above this many findings (default %d); "
                        "guards against a mis-firing rule flooding the queue "
                        "rather than reporting real drift" % FINDING_BUDGET)

    args = ap.parse_args(argv)

    if args.cmd != "lint":  # pragma: no cover - argparse enforces the set
        ap.error("unknown command")

    findings = lint_repo(args.root)
    budget_error = check_budget(findings, args.max_findings)
    if args.kind:
        findings = [f for f in findings if f["kind"] == args.kind]

    if args.quiet:
        return 1 if findings else 0

    if budget_error:
        # Printed before the findings: a flood is the headline, not the list.
        print("ERROR: " + budget_error, file=sys.stderr)

    if args.json:
        print(json.dumps(findings, indent=2))
    elif args.report:
        print(_report(findings, args.root))
    else:
        root = args.root or os.path.join(os.path.dirname(__file__), "..", "..")
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