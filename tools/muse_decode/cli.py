"""muse-decode CLI: `.mu` container → event stream summary.

Usage:
  python3 tools/muse_decode/cli.py file.mu
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from muse_decode import decode, DecodeError  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("container", help=".mu container path")
    args = ap.parse_args(argv)
    try:
        work = decode(args.container)
    except DecodeError as e:
        print(f"FAIL  decode: {e}")
        return 1
    print(f"OK  {args.container}: {len(work.parts)} parts, {work.note_count} notes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
