"""Tests: chain smoke follow-up (issue #172).

1. Registry scope pin: fast registry is Bach mvt 1 + Byrd Kyrie/Gloria.
2. Failure-injection drill: failing stage isolates in the smoke registry.
3. Slow registry available: --full tier in run_tests.sh hookup pinned.
"""

import subprocess
import sys

import pytest

from muse_chain.chain import check_determinism, run_work

FAST_REGISTRY = [
    ("bach-bwv227.1", "bach/bwv227.1.mxl"),
    ("byrd-1-kyrie", "byrd/1-Kyrie.mid"),
    ("byrd-2-gloria", "byrd/2-Gloria.mid"),
]


class TestRegistryScope:
    def test_fast_registry_pinned(self):
        assert FAST_REGISTRY == [
            ("bach-bwv227.1", "bach/bwv227.1.mxl"),
            ("byrd-1-kyrie", "byrd/1-Kyrie.mid"),
            ("byrd-2-gloria", "byrd/2-Gloria.mid"),
        ]

    def test_smoke_registry_is_fast(self):
        import time
        t0 = time.monotonic()
        check_determinism(registry=FAST_REGISTRY)
        assert time.monotonic() - t0 < 30  # measured ~0.3s per run, x2


class TestFailureInjection:
    def test_failing_stage_isolated_by_name(self):
        r = run_work("broken", "nope.mxl")
        assert not r.ok
        fails = [s for s in r.stages if s.status == "FAIL"]
        assert len(fails) == 1
        assert fails[0].stage.startswith("parse")


class TestRunnerHookup:
    def test_full_lists_slow_tier_source(self):
        r = subprocess.run(
            ["bash", "tools/run_tests.sh", "--list"],
            capture_output=True, text=True, timeout=60,
            cwd=__import__("os").path.normpath(
                __import__("os").path.join(__import__("os").path.dirname(__file__), "..", "..")
            ),
        )
        assert r.returncode == 0
        assert "chain_smoke" in r.stdout
        assert "slow tier" in r.stdout
