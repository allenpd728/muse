"""S3.7 lineage fields on seed provenance (issue #255; spec
tests/open_20260825-235500_s3-7-lineage-fields.md).

Code under test: tools/muse_seed/seed.py `_validate_provenance` —
optional `extends` (bare 64-hex sha256) and `operation` (tool@version);
all other provenance keys free-form.
"""

import os
import subprocess
import sys

import pytest

from muse_seed import Seed, SeedError, dump_seed, load_seed, validate_seed

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
SEEDS_DIR = os.path.join(REPO, "seeds")
WORK = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")

GOOD_HASH = "a" * 64
GOOD_HASH_2 = "0123456789abcdef" * 4


def _seed(**prov_extra):
    prov = {"author": "test", "ai_assisted": False}
    prov.update(prov_extra)
    return Seed(
        format_version="0.1",
        work_id="t",
        params={"tempo": {"min_bpm": 60, "max_bpm": 120}},
        assertions={"tempo_bounds": {"min_bpm": 60, "max_bpm": 120}},
        provenance=prov,
    )


# --- 1. Acceptance matrix ---

def test_no_lineage_fields_valid():
    validate_seed(_seed())


def test_extends_only_valid():
    validate_seed(_seed(extends=GOOD_HASH))


def test_operation_only_valid():
    validate_seed(_seed(operation="muse_distill@1"))


def test_both_fields_valid_and_round_trip():
    seed = _seed(extends=GOOD_HASH_2, operation="muse_author@1.2.3")
    for fmt in ("yaml", "json"):
        loaded = load_seed(dump_seed(seed, fmt=fmt), fmt=fmt)
        assert loaded.provenance["extends"] == GOOD_HASH_2
        assert loaded.provenance["operation"] == "muse_author@1.2.3"


# --- 2. extends rejection ---

@pytest.mark.parametrize("bad", [
    "a" * 63,                      # too short
    "a" * 65,                      # too long
    "g" * 64,                      # non-hex
    f"sha256:{GOOD_HASH}",         # prefixed digest is NOT the convention
    123,                           # non-string
    [GOOD_HASH],                   # list
])
def test_extends_rejected(bad):
    with pytest.raises(SeedError, match="extends"):
        validate_seed(_seed(extends=bad))


def test_extends_accepts_uppercase_hex():
    """Uppercase hex is sanctioned — is_sha256_hex documents
    'lowercase-or-upper' as the manifest's shape."""
    validate_seed(_seed(extends=GOOD_HASH.upper()))


# --- 3. operation rejection ---

@pytest.mark.parametrize("bad", [
    "Distill@1",        # capitalized tool
    "muse_distill",     # missing version
    "@1",               # missing tool
    "muse distill@1",   # space in name
    "muse_distill@x",   # non-numeric version
    42,                 # non-string
])
def test_operation_rejected(bad):
    with pytest.raises(SeedError, match="operation"):
        validate_seed(_seed(operation=bad))


@pytest.mark.parametrize("good", ["muse_distill@1", "muse_author@1.2.3", "a@0"])
def test_operation_accepted_shapes(good):
    validate_seed(_seed(operation=good))


# --- 4. Non-breaking pin over committed seeds ---

def test_committed_seeds_validate_unchanged():
    seeds = [f for f in os.listdir(SEEDS_DIR) if f.endswith(".seed.yaml")]
    assert seeds, "no committed seeds found"
    for name in seeds:
        text = open(os.path.join(SEEDS_DIR, name)).read()
        seed = load_seed(text, fmt="yaml")  # raises on regression
        assert seed.work_id, name


# --- 5. CLI seam ---

def test_c1_validate_fails_on_malformed_extends(tmp_path, capsys):
    import yaml
    from muse_seed_cli.cli import _validate

    doc = yaml.safe_load(open(os.path.join(SEEDS_DIR, "bwv227.1.seed.yaml")).read())
    doc["provenance"]["extends"] = "not-a-hash"
    bad = tmp_path / "bad.seed.yaml"
    bad.write_text(yaml.safe_dump(doc, sort_keys=False))
    rc = _validate(str(bad), WORK)
    assert rc == 1
    assert "extends" in capsys.readouterr().out
