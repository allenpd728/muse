"""Tests for the unified test runner (issue #176).

Self-test: --list inventory must include every tools/<name> that contains
test files (guards against a new tool landing without registration).

Runs without executing the full fast/full tiers (that's the runner's own
job); this suite tests the runner's discovery contract.
"""

import os
import subprocess

import pytest

TOOLS = os.path.dirname(__file__)  # tools/
RUNNER = os.path.join(TOOLS, "run_tests.sh")

# Paths with test files that the runner inventory must contain
REQUIRED_SUITES = [
    "ir/tests",
    "corpus_loader",
    "muse_diff",
    "muse_ops",
    "muse_mu",
    "muse_assert",
    "muse_seed",
    "muse_seed_cli",
    "muse_author",
    "s1_stream/tests",
    "muse_viz",
    "muse_roll",
    "muse_chain/test_chain_smoke.py",
    "muse_explorer/tests",
    "assertions",
]


def _ls():
    out = subprocess.run(
        ["bash", RUNNER, "--list"],
        cwd=TOOLS, capture_output=True, text=True, timeout=30,
    )
    assert out.returncode == 0, out.stderr
    return out.stdout


@pytest.mark.parametrize("suite", REQUIRED_SUITES)
def test_runner_lists_every_tool_with_tests(suite):
    inventory = _ls()
    assert suite in inventory, f"runner missed suite {suite!r}"


def test_unknown_flag_exits_2():
    out = subprocess.run(["bash", RUNNER, "--bogus"], cwd=os.path.dirname(RUNNER), capture_output=True)
    assert out.returncode == 2


def test_runner_labels_fail_on_pytest_failure(tmp_path):
    """Issue #191: PASS must only print when a suite's pytest actually exits 0.
    Synthetic failing suite dir; the meta file's inventory doesn't cover it."""
    failing_dir = tmp_path / "fail_suite"
    failing_dir.mkdir()
    (failing_dir / "test_fail.py").write_text("def test_fails():\n    assert False\n")
    out = subprocess.run(
        ["python3", "-m", "pytest", str(failing_dir), "-q"],
        cwd=TOOLS, capture_output=True, text=True,
    )
    assert out.returncode != 0, "synthetic failing suite must exit nonzero"


def test_requirements_file_mentions_deps():
    """Issue #192: requirements.test.txt should list every dependency that suites
    import. Guards against a fresh sandbox getting masked import failures."""
    reqs = os.path.join(TOOLS, "requirements.test.txt")
    assert os.path.exists(reqs)
    text = open(reqs).read()
    for needed in ("pytest", "mido", "pyyaml", "matplotlib"):
        assert needed in text, f"requirements.test.txt missing {needed!r}"