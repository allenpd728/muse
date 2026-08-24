"""C1 CLI: validate a seed against its corpus work; budget-check; assert.

Usage:
  python3 tools/muse_seed_cli/cli.py validate <seed.yaml> <work>
  python3 tools/muse_seed_cli/cli.py budget-check <era> [--nominal-bpm N]
  python3 tools/muse_seed_cli/cli.py read <seed.yaml>
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from muse_ir import load as load_work  # noqa: E402
from muse_seed import (  # noqa: E402
    Seed, load_seed, dump_seed, validate_seed, SeedError,
)
from muse_seed.params import (  # noqa: E402
    ERA_BUDGETS, tempo_budget, velocity_budget, chord_spread_ms, RangeError,
)
from muse_assert import validate_assertions, AssertionError  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="C1 seed validator")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="validate a seed against a work")
    v.add_argument("seed", help="path to seed YAML")
    v.add_argument("work", help="path to corpus work (.xml/.mxl/.mid)")

    b = sub.add_parser("budget-check", help="check era-calibrated budgets")
    b.add_argument("era", choices=sorted(ERA_BUDGETS))
    b.add_argument("--nominal-bpm", type=int, default=96)

    r = sub.add_parser("read", help="read a seed file and print summary")
    r.add_argument("seed")

    args = ap.parse_args()

    if args.cmd == "validate":
        sys.exit(_validate(args.seed, args.work))
    if args.cmd == "budget-check":
        sys.exit(_budget_check(args.era, args.nominal_bpm))
    if args.cmd == "read":
        sys.exit(_read(args.seed))


def _validate(seed_path, work_path):
    errors = []
    try:
        text = open(seed_path).read()
        seed = load_seed(text, fmt="yaml")
    except (SeedError, Exception) as e:
        print(f"FAIL  schema: {e}")
        return 1
    print("OK  seed schema valid")

    # Authored proposals must carry the sanctioning budget (S3 decisions
    # log 2026-08-24; the auditability the field exists for).
    if seed.provenance.get("author") == "muse_author" and seed.era_budget is None:
        print("FAIL  authored proposal missing era_budget "
              "(provenance.author is muse_author — the budget that sanctioned "
              "the proposal must ride the seed)")
        return 1

    work = load_work(work_path)
    try:
        validate_assertions(work, seed.assertions)
        print("OK  assertions pass on work")
    except AssertionError as e:
        print(f"FAIL  assertions: {e}")
        errors.append(e)

    # budget sanity: tempo range within sane bounds
    tempo = seed.params.get("tempo", {})
    if tempo:
        lo, hi = tempo.get("min_bpm", 0), tempo.get("max_bpm", 300)
        if not (30 <= lo <= hi <= 300):
            print(f"WARN  tempo bounds [{lo}, {hi}] outside sane range")

    _budget_era_check(seed)

    if errors:
        print(f"FAIL  {len(errors)} assertion(s) violated")
        return 1
    print("OK  seed validates against work")
    return 0


def _budget_era_check(seed):
    era = seed.provenance.get("era") or seed.provenance.get("style")
    if not era:
        return
    if era not in ERA_BUDGETS:
        print(f"WARN  unknown era '{era}' in provenance; budgets not checked")
        return
    tempo = seed.params.get("tempo", {})
    nominal = tempo.get("default_bpm", 96)
    budget = tempo_budget(era, nominal)
    lo, hi = tempo.get("min_bpm"), tempo.get("max_bpm")
    if lo and hi:
        if lo < budget.min_bpm or hi > budget.max_bpm:
            print(f"WARN  seed tempo [{lo}..{hi}] outside {era} budget "
                  f"[{budget.min_bpm}..{budget.max_bpm}]")
        else:
            print(f"OK  tempo [{lo}..{hi}] within {era} budget "
                  f"[{budget.min_bpm}..{budget.max_bpm}]")


def _budget_check(era, nominal_bpm):
    try:
        t = tempo_budget(era, nominal_bpm)
        v = velocity_budget(era)
        c = chord_spread_ms(era)
        print(f"OK  {era}: tempo [{t.min_bpm}..{t.max_bpm}] default {t.default_bpm}, "
              f"velocity ±{v:.0%}, chord spread {c}ms")
        return 0
    except RangeError as e:
        print(f"FAIL  {e}")
        return 1


def _read(seed_path):
    try:
        text = open(seed_path).read()
        seed = load_seed(text, fmt="yaml")
    except Exception as e:
        print(f"FAIL  {e}")
        return 1
    print(f"work_id: {seed.work_id}")
    print(f"title: {seed.title}")
    print(f"params: {list(seed.params)}")
    print(f"philosophy: {list(seed.philosophy)}")
    print(f"variation_points: {len(seed.variation_points)}")
    print(f"assertions: {list(seed.assertions)}")
    return 0


if __name__ == "__main__":
    main()
