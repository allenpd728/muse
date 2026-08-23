"""S3.3 philosophy adversarials + YAML path + vocabulary tripwire (issue #149).

Gap 1: identity guard against hyphenated/lowercase impersonations, three-name
phrases, era-whitelisted names. "like bach" passes only because impersonation
is lowercase; the guard's case-folding decision is pinned here.
Gap 2: philosophy validation through load_seed(fmt="yaml") end-to-end.
Gap 3: VOCABULARY is additive-only — the tripwire that protects existing seeds.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_seed.philosophy import FIELDS, VOCABULARY, Philosophy, PhilosophyError
from muse_seed.seed import load_seed


def _prov(**extra):
    base = {"author": "agent", "ai_assisted": True}
    base.update(extra)
    return base


def _phil(entries, prov=None):
    p = Philosophy(entries=entries, provenance=prov or _prov())
    p.validate()
    return p


# --- Gap 1: identity-guard adversarial sweep ---

@pytest.mark.parametrize(
    "value",
    [
        "like Bach",  # impersonation with capital start
        "in the style of Bach",
        "After Mozart",
        "Glenn Gould's detache",
        "Second Viennese&Brahms",
    ],
)
def test_suspected_identity_needs_license(value):
    with pytest.raises(PhilosophyError, match="suspected artist identity"):
        _phil({"tempo_philosophy": [value]})


def test_lowercase_impersonation_is_free_text(value="like bach"):
    """Lowercase impersonation stays free-text: pinning the guard's
    case-folding decision (see spec — locale table deferred)."""
    _phil({"tempo_philosophy": [value]})  # no raise


def test_three_name_identity_flagged():
    with pytest.raises(PhilosophyError, match="suspected artist identity"):
        _phil({"dynamic_philosophy": ["Johann Sebastian Bach Crucifixus"]})


def test_license_ref_unblocks_with_provenance():
    phil = _phil(
        {"tempo_philosophy": ["Glenn Gould extreme slow rendering"]},
        prov=_prov(license_ref="glenn-gould-estate"),
    )
    assert phil.to_dict()["provenance"]["license_ref"] == "glenn-gould-estate"


@pytest.mark.parametrize("era", ["Viennese Classical", "Roman School", "Mannheim School"])
def test_era_names_survive(era):
    _phil({"articulation_stance": [era + " rhetoric"]})


@pytest.mark.parametrize("era", ["Viennese Classical", "Roman School", "Mannheim School"])
def test_era_names_survive(era):
    _phil({"articulation_stance": [era + " rhetoric"]})


def test_hyphenated_pair_flagged():
    """Surname pairs are caught by the extended regex."""
    with pytest.raises(PhilosophyError, match="suspected artist identity"):
        _phil({"tempo_philosophy": ["Bach-and-Handel shorthand"]})


# --- Gap 2: YAML path coverage ---

YAML_SEED = """
format_version: "0.3"
work_id: bach-bwv227
params:
  tempo_arc: [1.0]
assertions:
  must_contain: ["x"]
philosophy:
  tempo_philosophy: ["flexible"]
  dynamic_philosophy: ["terraced"]
  provenance:
    author: openhands
    ai_assisted: true
"""


def test_load_seed_yaml_path_runs_philosophy_validation():
    seed = load_seed(YAML_SEED, fmt="yaml")
    assert seed.philosophy["tempo_philosophy"] == ["flexible"]


def test_load_seed_yaml_rejects_unlicensed_identity():
    bad = YAML_SEED.replace('["flexible"]', '["After Mozart"]')
    with pytest.raises(Exception):
        load_seed(bad, fmt="yaml")


def test_load_seed_yaml_requires_provenance():
    bad = YAML_SEED.replace("  provenance:\n    author: openhands\n    ai_assisted: true\n", "")
    with pytest.raises(Exception):
        load_seed(bad, fmt="yaml")


# --- Gap 3: vocabulary drift tripwire ---

PUBLIC_VOCABULARY_BASELINE = {
    "flexible", "architectural", "strict", "rubato", "dance-pulse",
    "terraced", "dramatic", "restrained", "hairpin-led",
    "consort", "breathe-at-cadences", "detached", "legato-led", "rhetorical",
    "sparse", "improvised", "written-out", "none",
    "soloistic", "blended", "antiphonal",
}


def test_vocabulary_is_additive_only():
    """Existing seeds must never break: the baseline may only grow."""
    assert PUBLIC_VOCABULARY_BASELINE <= set(VOCABULARY)


def test_vocabulary_no_duplicates_across_fields():
    all_vals = set(VOCABULARY)
    assert len(all_vals) == len(VOCABULARY)
