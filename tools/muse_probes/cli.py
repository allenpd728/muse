"""muse-probes CLI: compute the probe set for a seed against its work.

    python3 tools/muse_probes/cli.py <seed.yaml> [--work <corpus-file>]
    python3 tools/muse_probes/cli.py <seed.yaml> --prior <prior-seed.yaml>
    python3 tools/muse_probes/cli.py <seed.yaml> --era baroque

Exit 0 when the report's gate probes pass (fidelity + determinism +
assertions); 1 otherwise. JSON to stdout or --out.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))

from muse_ir import load as load_work  # noqa: E402
from muse_seed import load_seed  # noqa: E402

from muse_probes.probes import compute_probes  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve(path):
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-probes", description=__doc__)
    ap.add_argument("seed", help="seed YAML path")
    ap.add_argument("--work", help="corpus file override (default: seed's provenance.source)")
    ap.add_argument("--prior", help="prior seed revision for the param diff probe")
    ap.add_argument("--era", default="baroque", help="era for budget fit")
    ap.add_argument("--out", help="write probe JSON here instead of stdout")
    args = ap.parse_args(argv)

    seed = load_seed(open(_resolve(args.seed)).read(), fmt="yaml")
    work_path = args.work or getattr(seed, "provenance", {}).get("source")
    if not work_path:
        print("no work: seed.provenance.source missing and --work not given",
              file=sys.stderr)
        return 2
    work = load_work(_resolve(work_path))
    prior = load_seed(open(_resolve(args.prior)).read(), fmt="yaml") if args.prior else None

    report = compute_probes(seed, work, prior_seed=prior, era=args.era,
                            seed_path=_resolve(args.seed))
    out = report.to_json()
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(out)
        print(f"wrote {args.out} (ok={report.ok})")
    else:
        print(out, end="")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
