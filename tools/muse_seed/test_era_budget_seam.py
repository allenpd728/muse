"""era_budget at the Seed/YAML seam (issue #236; S3 decisions log
2026-08-24): the optional field round-trips, stays absent when unset,
rejects non-mappings, rides authored proposals end-to-end, and C1
requires it on muse_author proposals."""

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "muse_seed"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "muse_seed_cli"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "assertions"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "muse_budgets"))

from muse_seed import Seed, SeedError, dump_seed, load_seed, validate_seed  # noqa: E402
from muse_seed_cli.cli import _validate  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")
SEED_YAML = os.path.join(REPO, "seeds", "bwv227.1.seed.yaml")

BUDGET = {"tempo_bpm": {"min": 88, "max": 120}, "source": "muse_budgets"}


def _minimal_seed(**kw):
    return Seed(
        format_version="0.1",
        work_id="t",
        params={"tempo": {"min_bpm": 60, "max_bpm": 120}},
        assertions={"tempo_bounds": {"min_bpm": 60, "max_bpm": 120}},
        **kw,
    )


# --- Schema behavior ---

def test_era_budget_round_trips_yaml_and_json():
    seed = _minimal_seed(era_budget=BUDGET)
    for fmt in ("yaml", "json"):
        loaded = load_seed(dump_seed(seed, fmt=fmt), fmt=fmt)
        assert loaded.era_budget == BUDGET


def test_absent_era_budget_stays_absent():
    out = dump_seed(_minimal_seed())
    assert "era_budget" not in out
    assert load_seed(out).era_budget is None


def test_non_mapping_era_budget_rejected():
    with pytest.raises(SeedError, match="era_budget must be a mapping"):
        validate_seed(_minimal_seed(era_budget="baroque"))


def test_era_budget_is_a_known_top_level_key():
    # Guard against the field being dropped from TOP_LEVEL_KEYS silently —
    # an unknown-key failure here means the schema lost the field.
    validate_seed(_minimal_seed(era_budget=BUDGET))


# --- C1 presence assertion on authored proposals ---

def _authored_variant(tmp_path, with_budget):
    import yaml
    doc = yaml.safe_load(open(SEED_YAML).read())
    doc["provenance"]["author"] = "muse_author"
    if with_budget:
        doc["era_budget"] = BUDGET
    path = tmp_path / ("with.yaml" if with_budget else "without.yaml")
    path.write_text(yaml.safe_dump(doc, sort_keys=False))
    return str(path)


def test_c1_rejects_authored_proposal_missing_era_budget(tmp_path, capsys):
    rc = _validate(_authored_variant(tmp_path, with_budget=False), WORK)
    assert rc == 1
    assert "era_budget" in capsys.readouterr().out


def test_c1_accepts_authored_proposal_with_era_budget(tmp_path, capsys):
    rc = _validate(_authored_variant(tmp_path, with_budget=True), WORK)
    out = capsys.readouterr().out
    assert rc == 0, out


def test_c1_silent_on_hand_authored_seed_without_budget(capsys):
    """Hand-authored seeds (provenance.author != muse_author) are not
    required to carry the field — optional means optional."""
    rc = _validate(SEED_YAML, WORK)
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "era_budget" not in out


# --- Author CLI end-to-end ---

def test_author_cli_proposal_carries_era_budget(tmp_path):
    out = tmp_path / "p.yaml"
    r = subprocess.run(
        [sys.executable, os.path.join(REPO, "tools", "muse_author", "cli.py"),
         os.path.join(REPO, "corpus", "byrd", "1-Kyrie.mid"),
         "--era", "baroque", "--out", str(out)],
        capture_output=True, text=True, cwd=REPO,
    )
    # exit may be non-zero on pre-existing assertion drift; the seam under
    # test is the written YAML.
    text = out.read_text()
    assert "era_budget" in text, f"proposal dropped era_budget:\n{r.stdout}{r.stderr}"
    loaded = load_seed(text)
    assert loaded.era_budget["tempo_bpm"]["min"] == 88  # baroque floor
    assert loaded.provenance["author"] == "muse_author"
