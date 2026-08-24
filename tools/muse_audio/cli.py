"""muse-audio CLI: render seed revisions to workbench WAVs.

Usage:
  python3 tools/muse_audio/cli.py corpus/bach/bwv227.1.mxl \
      --seed seeds/bwv227.1.v1.seed.yaml --label v1
  python3 tools/muse_audio/cli.py corpus/bach/bwv227.1.mxl \
      --seed seeds/bwv227.1.v2.seed.yaml --label v2
  python3 tools/muse_audio/cli.py corpus/bach/bwv227.1.mxl \
      --seed seeds/bwv227.1.v2.seed.yaml --label llm --live
  python3 tools/muse_audio/cli.py --manifest   # after renders, rewrite the index
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))

from muse_audio.audio import AUDIO_DIR, MANIFEST_NAME, render_revision  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="muse-audio")
    ap.add_argument("work", nargs="?", help="corpus work (.mxl/.xml/.mid)")
    ap.add_argument("--seed", default=None, help="seed revision YAML")
    ap.add_argument("--label", default=None,
                    help="revision label (default: seed filename stem)")
    ap.add_argument("--live", action="store_true",
                    help="run the real L1.3 loop via GeminiProvider(live=True)")
    ap.add_argument("--out-dir", default=AUDIO_DIR)
    args = ap.parse_args(argv)

    if not args.work:
        ap.error("work is required")
    label = args.label
    if label is None:
        if not args.seed:
            ap.error("--label or --seed required")
        stem = os.path.splitext(os.path.basename(args.seed))[0]
        stem = stem.removesuffix(".seed")
        label = stem.split(".")[-1] if "." in stem else stem
    if args.live and not label.startswith("llm"):
        label = f"llm-{label}"

    r = render_revision(args.work, args.seed, label,
                        out_dir=args.out_dir, live=args.live)
    print(f"OK  {r.wav}  origin={r.origin}  {r.notes} notes  "
          f"{r.duration_sec}s  sha256 {r.sha256[:12]}…")
    print(f"next: run with --manifest companions then add to "
          f"docs/audio/{MANIFEST_NAME} via write_manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
