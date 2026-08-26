#!/usr/bin/env python3
"""Generate docs/boardroom/data/stats.json for the status dashboard (B3,
issue #265).

Counts are computed from the repo at generation time — the dashboard page
fetches this file, so the board sees current numbers, not hardcoded ones.
Re-run after suite/corpus changes (or wire into the workbench data regen).

Usage: python3 tools/boardroom_stats.py
"""

import json
import os
import re
import subprocess
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(REPO, "docs", "boardroom", "data", "stats.json")


def suite_counts():
    """Suite/test counts from the runner inventory + pytest collection.
    Suite count is authoritative (the runner's own list); test count is a
    cheap collect-only over the fast-tier dirs."""
    proc = subprocess.run(
        ["bash", os.path.join(REPO, "tools", "run_tests.sh"), "--list"],
        capture_output=True, text=True, cwd=os.path.join(REPO, "tools"),
    )
    suites = re.findall(r"^\s+(\w[\w-]*)=", proc.stdout, re.MULTILINE)
    return len(suites)


def test_count():
    """Collected tests across the fast-tier suite dirs (collect-only, no run)."""
    proc = subprocess.run(
        ["bash", os.path.join(REPO, "tools", "run_tests.sh"), "--list"],
        capture_output=True, text=True, cwd=os.path.join(REPO, "tools"),
    )
    dirs = re.findall(r"^\s+\w[\w-]*=(\S+)$", proc.stdout, re.MULTILINE)
    total = 0
    for d in dirs:
        p = os.path.join(REPO, "tools", d)
        if not os.path.isdir(p):
            p = os.path.dirname(p) if not p.endswith(".py") else p
            if not os.path.exists(p):
                continue
        r = subprocess.run(
            [sys.executable, "-m", "pytest", p, "--collect-only", "-q",
             "-m", "not slow"],
            capture_output=True, text=True, cwd=os.path.join(REPO, "tools"),
        )
        m = re.search(r"(\d+) tests? collected", r.stdout)
        if m:
            total += int(m.group(1))
    return total


def corpus_works():
    with open(os.path.join(REPO, "docs", "explorer", "data", "works.json")) as fh:
        return len(json.load(fh)["works"])


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    stats = {
        "format": "boardroom-stats-v1",
        "generated_by": "tools/boardroom_stats.py",
        "suites": suite_counts(),
        "tests_fast_tier": test_count(),
        "corpus_works": corpus_works(),
    }
    with open(OUT, "w") as fh:
        json.dump(stats, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"wrote {OUT}: {stats['suites']} suites, "
          f"{stats['tests_fast_tier']} fast-tier tests, "
          f"{stats['corpus_works']} corpus works")


if __name__ == "__main__":
    main()
