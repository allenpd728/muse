"""muse-event CLI: run the corpus ladder (E1 scaffold).

    python -m muse_event [--era classical] [--out event_dir]
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from .event import run_ladder  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="muse-event")
    ap.add_argument("--era", default="classical")
    ap.add_argument("--out", default="event")
    args = ap.parse_args(argv)

    ledger = run_ladder(args.out, era=args.era)
    print(f"{args.out}/event-ledger.json: {len(ledger['rungs'])} rungs")
    for r in ledger["rungs"]:
        mark = "✓" if r["ok"] else "×"
        print(f"  {mark} rung{r['rung']} {r['work_id']}{': ' + r['error'] if r['error'] else ''}")
    return 0 if all(r["ok"] for r in ledger["rungs"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
