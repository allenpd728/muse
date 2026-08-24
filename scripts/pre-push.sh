#!/usr/bin/env bash
# scripts/pre-push.sh — gate of record for pushes to dev.
#
# Runs the unified test runner's fast tier and refuses the push on failure.
# This is the repo's working gate until the GitHub Actions runner issue
# (issue #194) resolves — a private repo with no working CI can only gate
# honestly at the push point.
#
# Opt in once per checkout:
#   git config core.hooksPath scripts
#
# The hook is versioned here so every checkout shares it; enabling it is a
# deliberate local choice (hooks can't be forced by the repo).
set -euo pipefail

branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" != "dev" ]; then
  exit 0
fi

echo "pre-push gate: running fast tier (tools/run_tests.sh)..."
if ! ./tools/run_tests.sh; then
  echo ""
  echo "pre-push gate FAILED — fix the suite before pushing to dev." >&2
  echo "bypass (emergency only): git push --no-verify" >&2
  exit 1
fi
echo "pre-push gate passed."
