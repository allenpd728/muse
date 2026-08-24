#!/usr/bin/env bash
# tools/run_tests.sh — unified test runner (issue #167).
#
# One command runs every tool's pytest suite with a per-tool report and an
# aggregate exit code. Default is the fast tier (full green path minus the
# known-slow suites); --full runs everything incl. slow suites.
#
# Usage:
#   ./tools/run_tests.sh            # fast tier
#   ./tools/run_tests.sh --full     # everything (incl. slow)
#   ./tools/run_tests.sh --list     # show the suite list and exit
#
# Deps: python3 -m pip install -r tools/requirements.test.txt
set -u
cd "$(dirname "$0")"

# name:dir — dir relative to tools/. Suites are discovered on purpose, not
# by directory globbing: SPIKE and __pycache__ must stay out.
SUITES=(
  "ir:ir/tests"
  "corpus_loader:corpus_loader"
  "muse_diff:muse_diff"
  "muse_ops:muse_ops"
  "muse_unpack:muse_mu"
  "muse_assert:muse_assert"
  "muse_seed:muse_seed"
  "muse_seed_cli:muse_seed_cli"
  "muse_author:muse_author"
  "s1_stream:s1_stream/tests"
  "muse_viz:muse_viz"
  "muse_roll:muse_roll"
  "assertions:assertions/tests"
)
# Chain smoke (fast tier): e2e on the small registry, W4 verify PASS.
SUITES+=("chain_smoke:muse_chain/test_chain_smoke.py")
# Explorer (fast tier): artifact contract + determinism (quick mode).
SUITES+=("muse_explorer:muse_explorer/tests")
# Probes (fast tier): seed-iteration probe engine.
SUITES+=("muse_probes:muse_probes/tests")
# Generate loop (fast tier): schema, provider, generate, integration.
SUITES+=("muse_mockup:muse_mockup")
SUITES+=("muse_provider:muse_provider/tests")
SUITES+=("muse_generate:muse_generate/tests")
SUITES+=("muse_grow:muse_grow/tests")
# P1/P2/L-series (fast tier): decoder, renderer, mockup harness, A/B rig,
# distiller — all corpus-light.
SUITES+=("muse_decode:muse_decode/tests")
SUITES+=("muse_play:muse_play/tests")
SUITES+=("muse_render:muse_render/tests")
SUITES+=("muse_compare:muse_compare/tests")
SUITES+=("muse_distill:muse_distill/tests")
SUITES+=("muse_mockup:muse_mockup")
SLOW_SUITES=(
  "muse_analyze:muse_analyze"
  "muse_chain:muse_chain"
  "qa_frontend:qa_frontend/tests"
)

MODE=fast
LIST_ONLY=0
for a in "$@"; do
  case $a in
    --full) MODE=full ;;
    --list) LIST_ONLY=1 ;;
    *) echo "unknown flag: $a" >&2; exit 2 ;;
  esac
done

if [ $LIST_ONLY -eq 1 ]; then
  echo "fast tier:"
  for s in "${SUITES[@]}"; do echo "  ${s%%:*}=${s#*:}"; done
  echo "slow tier (--full adds):"
  for s in "${SLOW_SUITES[@]}"; do echo "  ${s%%:*}=${s#*:}"; done
  exit 0
fi

# Install deps upfront (issue #192). Pytest alone is not enough — a fresh
# sandbox sees import failures across suites without per-file deps; the
# requirements file is the source of truth.
python3 -c "import pytest, yaml, matplotlib" 2>/dev/null || {
  echo "installing test deps: pip install -q -r tools/requirements.test.txt" >&2
  python3 -m pip install -q -r tools/requirements.test.txt
}

run_one() {
  local name=$1 dir=$2
  local t0 t1 rc
  t0=$(date +%s)
  local tmp
  tmp=$(mktemp)
  # Run pytest directly (no pipeline) so $? reflects pytest, not tail.
  python3 -m pytest "$dir" -q >"$tmp" 2>&1
  rc=$?
  local out
  out=$(tail -3 "$tmp")
  rm -f "$tmp"
  t1=$(date +%s)
  local dur=$((t1 - t0))
  if [ $rc -eq 0 ]; then
    printf "PASS  %-16s %4ss    %s\n" "$name" "$dur" "$(echo "$out" | tail -1)"
  else
    printf "FAIL  %-16s %4ss    %s\n" "$name" "$dur" "$(echo "$out" | tail -1)"
  fi
  return $rc
}

failures=0
for s in "${SUITES[@]}"; do
  run_one "${s%%:*}" "${s#*:}" || failures=$((failures + 1))
done
if [ "$MODE" = "full" ]; then
  for s in "${SLOW_SUITES[@]}"; do
    run_one "${s%%:*}" "${s#*:}" || failures=$((failures + 1))
  done
fi

echo ""
if [ $failures -eq 0 ]; then
  echo "all suites green"
else
  echo "$failures suite(s) failed" >&2
fi
exit $failures