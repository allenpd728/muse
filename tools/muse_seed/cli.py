"""muse-seed CLI — C1 seed format implementation.

Validate a seed file against a corpus work: schema (S3.1), budget ranges
(S3.2), philosophy vocabulary (S3.3), variation points (S3.4), and
assertions against the loaded work (S3.5). Exit 0 valid, 1 invalid.

Usage:
  python3 tools/muse_seed/cli.py validate <seed.yaml> [--work <corpus-file>]
  python3 tools/muse_seed/cli.py show <seed.yaml>
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # tools/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))

from muse_ir import load  # noqa: E402
from muse_seed import SeedError, dump_seed, load_seed  # noqa: E402
from muse_seed.params import ERA_BUDGETS, RangeError, tempo_budget  # noqa: E402
from muse_seed.variation import validate_variation_points  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


class CLIError(ValueError):
    pass


def _read_seed(path):
    try:
        text = open(path).read()
    except OSError as e:
        raise CLIError(f"cannot read seed: {e}") from e
    try:
        return load_seed(text, fmt="yaml")
    except SeedError as e:
        raise CLIError(f"schema: {e}") from e


def _check_budgets(seed):
    """S3.2: tempo range must sit within some era's calibrated budget around
    its own default — a seed claiming freedom no era permits is suspicious."""
    tempo = seed.params.get("tempo")
    if not tempo:
        return "no tempo params (skipped)"
    try:
        nominal = int(tempo["default_bpm"])
        lo, hi = int(tempo["min_bpm"]), int(tempo["max_bpm"])
    except (KeyError, TypeError, ValueError) as e:
        raise CLIError(f"params.tempo malformed: {e}") from e
    if not (lo <= nominal <= hi):
        raise CLIError(f"tempo default {nominal} outside [{lo}, {hi}]")
    fits = []
    for era in ERA_BUDGETS:
        try:
            budget = tempo_budget(era, nominal)
        except RangeError:
            continue
        if budget.min_bpm <= lo and hi <= budget.max_bpm:
            fits.append(era)
    if not fits:
        raise CLIError(
            f"tempo range [{lo}, {hi}] around {nominal} exceeds every era "
            f"budget ({', '.join(sorted(ERA_BUDGETS))})")
    return f"tempo [{lo}, {hi}] @ {nominal} fits era budgets: {', '.join(sorted(fits))}"


def cmd_validate(args):
    seed = _read_seed(args.seed)
    print(f"OK  schema (S3.1) + philosophy (S3.3) + variation points (S3.4): {args.seed}")
    print(f"OK  budgets (S3.2): {_check_budgets(seed)}")

    work_path = args.work
    if work_path is None:
        # default: resolve the seed's provenance source inside the repo
        src = seed.provenance.get("source", "")
        candidate = os.path.join(REPO, src)
        if src and os.path.exists(candidate):
            work_path = candidate
    if work_path:
        work = load(work_path)
        validate_variation_points(seed.variation_points,
                                  duration_ticks=work.duration_ticks())
        print(f"OK  variation regions within work ({work.duration_ticks()} ticks)")
        from muse_assert import validate_assertions, AssertionError

        try:
            validate_assertions(work, seed.assertions)
        except AssertionError as e:
            raise CLIError(f"assertions (S3.5): {e}") from e
        print(f"OK  assertions (S3.5) against {os.path.basename(work_path)}")
    else:
        print("--  no work resolved; assertion check skipped")
    print("VALID")
    return 0


def cmd_show(args):
    seed = _read_seed(args.seed)
    print(dump_seed(seed, fmt="yaml"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-seed", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_val = sub.add_parser("validate", help="validate a seed against a corpus work")
    p_val.add_argument("seed")
    p_val.add_argument("--work", default=None, help="corpus file (default: seed provenance source)")
    p_show = sub.add_parser("show", help="canonical re-serialization of a seed")
    p_show.add_argument("seed")
    args = ap.parse_args(argv)
    try:
        return {"validate": cmd_validate, "show": cmd_show}[args.cmd](args)
    except CLIError as e:
        print(f"INVALID: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
