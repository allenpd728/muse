"""muse-rehearse CLI: parse a directive, dry-run the compiled delta, commit.

    python3 tools/muse_rehearse/cli.py dry-run <seed.yaml> "phrase: quieter at bar 8"
    python3 tools/muse_rehearse/cli.py commit <seed.yaml> <slug> "rebalance: bring P1 up at bar 8"

dry-run prints the param diff the commit would make (writes nothing).
commit writes the directive file + revision and re-stamps lineage.
Exit 0 ok; 1 on a grammar error (with the valid vocabulary).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))

from muse_ir import load as load_work  # noqa: E402
from muse_seed import load_seed  # noqa: E402

from muse_rehearse import (  # noqa: E402
    DirectiveError, parse_directive, dry_run, commit_directive,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve(path):
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def _load(seed_path):
    seed = load_seed(open(_resolve(seed_path)).read(), fmt="yaml")
    src = seed.provenance.get("source")
    work = load_work(_resolve(src)) if src else None
    return seed, work


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-rehearse", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dry-run", help="compile + show the param diff")
    d.add_argument("seed")
    d.add_argument("directive")
    d.add_argument("--era", default="baroque")

    c = sub.add_parser("commit", help="write directive + revision, stamp lineage")
    c.add_argument("seed")
    c.add_argument("slug")
    c.add_argument("directive")
    c.add_argument("--era", default="baroque")

    args = ap.parse_args(argv)
    seed, work = _load(args.seed)

    try:
        directive = parse_directive(args.directive, seed=seed, work=work)
    except DirectiveError as e:
        print(f"directive error: {e}", file=sys.stderr)
        return 1

    if args.cmd == "dry-run":
        _, diff = dry_run(directive, seed, args.era, work)
        print(json.dumps(diff, indent=2))
        return 0

    dpath, spath = commit_directive(
        directive, _resolve(args.seed), args.slug,
        era=args.era, repo_root=REPO, work=work)
    print(f"directive: {os.path.relpath(dpath, REPO)}")
    print(f"revision:  {os.path.relpath(spath, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
