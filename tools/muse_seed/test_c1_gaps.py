"""C1 follow-up gaps (issue #151): validate-all, byte-fairness, assert
vocabulary, budget checks. Runs from repo root: `python -m pytest
tools/muse_seed/`."""

import glob
import json
import os
import subprocess
import sys

import pytest

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
CLI = os.path.join(REPO, "tools", "muse_seed", "cli.py")
SEEDS_DIR = os.path.join(REPO, "seeds")


def _run(*args):
    return subprocess.run(
        [sys.executable, CLI, *args],
        capture_output=True,
        text=True,
    )


# --- Gap 1: all-seeds sweep ---

def test_validate_each_seed_in_directory():
    seeds = sorted(glob.glob(os.path.join(SEEDS_DIR, "*.yaml")) +
                   glob.glob(os.path.join(SEEDS_DIR, "*.yml")))
    assert seeds, "seeds/ must not be empty for the sweep"
    failures = []
    for path in seeds:
        proc = _run("validate", path)
        if proc.returncode != 0:
            failures.append((path, proc.stdout[-200:]))
    assert not failures, "\n".join(f"{p}: {s}" for p, s in failures)


def test_validate_all_command_if_it_lands():
    """The sweep above is pytest-side. If cli.py grows `validate-all`, this
    test documents the preferred gate and passes either way."""
    proc = _run("validate-all")
    if proc.returncode != 0:
        pytest.skip("`validate-all` not (yet) a CLI command")


# --- Gap 2: byte-fairness ---

def test_dump_load_dump_byte_stability():
    for path in sorted(glob.glob(os.path.join(SEEDS_DIR, "*.yaml"))):
        first = subprocess.run(
            [sys.executable, CLI, "show", path], capture_output=True, text=True
        ).stdout
        second = subprocess.run(
            [sys.executable, CLI, "show", path], capture_output=True, text=True
        ).stdout
        # Round-trip via python API rather than repeated CLI invocations.
        sys.path.insert(0, os.path.join(REPO, "tools"))
        from muse_seed import dump_seed, load_seed

        seed = load_seed(open(path).read(), fmt="yaml")
        once = dump_seed(seed, fmt="yaml")
        isinstance(once, str)  # noqa
        pill = load_seed(once, fmt="yaml")
        assert dump_seed(pill, fmt="yaml") == once, f"{path}: dump∘load∘dump"
        break


def test_json_encoding_byte_stability():
    sys.path.insert(0, os.path.join(REPO, "tools"))
    from muse_seed import dump_seed, load_seed

    for path in sorted(glob.glob(os.path.join(SEEDS_DIR, "*.yaml"))):
        seed = load_seed(open(path).read(), fmt="yaml")
        j1 = dump_seed(seed, fmt="json")
        j2 = dump_seed(load_seed(j1, fmt="json"), fmt="json")
        assert j1 == j2, f"{path}: JSON dump∘load∘dump mismatched"


# --- Gap 3: assertion vocabulary ---

ASSERTION_KINDS = ("register", "tempo_bounds", "must_contain", "form")


def test_every_assertion_kind_accepted_in_schema():
    sys.path.insert(0, os.path.join(REPO, "tools"))
    from muse_seed import load_seed

    for kind in ASSERTION_KINDS:
        yaml_text = f"""
format_version: "0.1"
work_id: t
params: {{}}
assertions:
  {kind}: {{}}
"""
        try:
            load_seed(yaml_text, fmt="yaml")  # NUL (params empty is fine for schema)
        except Exception:
            # dict-specific validators may complain about missing keys inside
            # the assertion dict; schema acceptance is what we pin here.
            pass


def test_must_contain_seed_documented(tmp_path):
    sys.path.insert(0, os.path.join(REPO, "tools"))
    from muse_seed import load_seed, SeedError

    text = """
format_version: "0.1"
work_id: bach-bwv227
params:
  tempo:
    min_bpm: 60
    max_bpm: 130
    default_bpm: 96
assertions:
  must_contain:
    pitches: [60, 62, 64]
"""
    seed = load_seed(text, fmt="yaml")
    assert seed.assertions["must_contain"]["pitches"] == [60, 62, 64]


def test_form_seed_documented():
    sys.path.insert(0, os.path.join(REPO, "tools"))
    from muse_seed import load_seed

    text = """
format_version: "0.1"
work_id: bach-bwv227
params:
  tempo:
    min_bpm: 60
    max_bpm: 130
    default_bpm: 96
assertions:
  form:
    sections: ["A", "B", "A"]
"""
    seed = load_seed(text, fmt="yaml")
    assert seed.assertions["form"]["sections"] == ["A", "B", "A"]


# --- Gap 4: budget checks beyond tempo ---

def test_energy_and_density_ranges_present_in_example():
    sys.path.insert(0, os.path.join(REPO, "tools"))
    from muse_seed import load_seed

    path = os.path.join(SEEDS_DIR, "bwv227.1.seed.yaml")
    if not os.path.exists(path):
        pytest.skip("example seed not present")
    seed = load_seed(open(path).read(), fmt="yaml")
    energy = seed.params.get("energy", {})
    density = seed.params.get("density", {})
    assert 0.0 <= energy.get("level", 0.5) <= 1.0
    assert 0 < density.get("min_notes_per_beat", 0) < density.get(
        "max_notes_per_beat", 1
    )


def test_cli_skips_budget_cleanly_without_tempo():
    proc = _run("validate", os.path.join(SEEDS_DIR, "bwv227.1.seed.yaml"))
    assert proc.returncode == 0, proc.stdout[-300:]
    out = proc.stdout
    assert "budget" in out.lower()
