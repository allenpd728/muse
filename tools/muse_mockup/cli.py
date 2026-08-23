"""muse-mockup CLI: generate mockup from work IR, validate via C1/#148.

Usage:
  python3 tools/muse_mockup/cli.py <work> [--era classical|romantic|...]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from muse_ir import load  # noqa: E402
from muse_mockup import Mockup, Note, add_note, validate_mockup, dump_mockup  # noqa: E402
from muse_seed import Seed  # noqa: E402


def _skips_rest_or_unpitched(n):
    return (n.pitch is None
            or getattr(n, "is_rest", False)
            or getattr(n, "is_unpitched", False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    work = load(args.work)
    meta = getattr(work, "meta", None)
    work_id = _getattr_meta(meta, "work_id", None) or "unknown"
    mockup = Mockup(work_id=work_id)

    for p in work.parts:
        for n in p.notes:
            if _skips_rest_or_unpitched(n):
                continue
            add_note(mockup, Note(pitch=n.pitch, onset=n.onset, duration=n.duration,
                                  velocity=64, part=p.id))
    mockup.validate()

    out = args.out or f"{os.path.splitext(os.path.basename(args.work))[0]}.mockup.json"
    with open(out, "w") as f:
        f.write(dump_mockup(mockup))
    print(f"OK  mockup written: {out} ({len(mockup.notes)} notes)")

    # human-validated assertions (no fail if empty)
    validate_mockup(mockup, {"assertions": {}})
    return 0


def _getattr_meta(meta, key, default=None):
    if meta is None:
        return default
    if key == "work_id":
        return getattr(meta, "title", None) or getattr(meta, "source_format", None) or default
    return getattr(meta, key, default)


if __name__ == "__main__":
    main()
