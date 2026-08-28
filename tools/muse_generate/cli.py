"""muse-generate CLI: assemble the L1 prompt for a seed (W-B10, #294).

    python3 tools/muse_generate/cli.py prompt <seed.yaml> [--era baroque]

Prints the assembled L1 prompt to stdout — the conversation answers it
(the ManualProvider path); the workbench pane shows it for the chat-only
transport. Exit 0 ok, 1 on error.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))

from muse_ir import load as load_work  # noqa: E402
from muse_seed import load_seed  # noqa: E402

from muse_generate import assemble_prompt  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve(path):
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-generate", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompt", help="assemble + print the L1 prompt")
    p.add_argument("seed")
    p.add_argument("--era", default="baroque")
    args = ap.parse_args(argv)

    if args.cmd != "prompt":
        return 1
    seed = load_seed(open(_resolve(args.seed)).read(), fmt="yaml")
    src = seed.provenance.get("source")
    work = load_work(_resolve(src))
    print(assemble_prompt(seed, work, era=args.era))
    return 0


if __name__ == "__main__":
    sys.exit(main())
