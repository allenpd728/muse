"""muse-lineage CLI: walk or verify an artifact's lineage chain.

    python3 tools/muse_lineage/cli.py walk <seed.yaml> [--store DIR ...]
    python3 tools/muse_lineage/cli.py verify <child> <parent>

walk prints one line per hop (child → status → parent) and JSON with
--json. Exit 0 when every hop is verified/root; 1 on missing/mismatch;
2 on usage or parse errors.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_lineage.lineage import (  # noqa: E402
    LineageError, verify_pair, walk,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-lineage", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("walk", help="walk the chain backward from a seed revision")
    w.add_argument("seed")
    w.add_argument("--store", action="append", default=None,
                   help="directory of candidate parents (default: repo seeds/)")
    w.add_argument("--json", action="store_true", help="emit JSON")

    v = sub.add_parser("verify", help="explicit pair check: child vs named parent")
    v.add_argument("child")
    v.add_argument("parent")

    args = ap.parse_args(argv)

    if args.cmd == "walk":
        return _walk(args)
    return _verify(args)


def _walk(args):
    dirs = args.store or [os.path.join(REPO, "seeds")]
    try:
        hops = walk(args.seed, dirs)
    except LineageError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"ok": all(h.status in ("verified", "root") for h in hops),
                          "hops": [h.to_dict() for h in hops]}, indent=2))
    else:
        for h in hops:
            arrow = f" -> {h.parent}" if h.parent else ""
            print(f"{h.status:9s} {h.child}{arrow}")
    return 0 if all(h.status in ("verified", "root") for h in hops) else 1


def _verify(args):
    try:
        status = verify_pair(args.child, args.parent)
    except LineageError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(status)
    return 0 if status == "verified" else 1


if __name__ == "__main__":
    sys.exit(main())
