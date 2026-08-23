"""S3.3 philosophy vocabulary tests (issue #144).

Typed-lite vocab (closed field set, known values + free-text escape),
provenance requirements, and the no-artist-lookalikes identity guard.
"""

import pytest

from muse_seed.philosophy import FIELDS, VOCABULARY, Philosophy, PhilosophyError
from muse_seed.seed import Seed, SeedError, validate_seed

PROV = {"author": "founder", "ai_assisted": False}


def phil(entries, prov=PROV):
    p = Philosophy(entries=entries, provenance=dict(prov))
    p.validate()
    return p


class TestVocabulary:
    def test_typed_values_accepted(self):
        phil({"tempo_philosophy": ["flexible", "architectural"],
              "dynamic_philosophy": ["terraced"]})

    def test_free_text_escape_accepted(self):
        phil({"articulation_stance": ["like a consort of viols at evensong"]})

    def test_unknown_field_rejected(self):
        with pytest.raises(PhilosophyError, match="unknown philosophy fields"):
            phil({"vibe": ["good"]})

    def test_empty_block_rejected(self):
        with pytest.raises(PhilosophyError, match="empty"):
            phil({})

    def test_empty_list_rejected(self):
        with pytest.raises(PhilosophyError, match="non-empty list"):
            phil({"tempo_philosophy": []})

    def test_blank_string_rejected(self):
        with pytest.raises(PhilosophyError, match="non-empty strings"):
            phil({"tempo_philosophy": ["  "]})

    def test_vocabulary_is_additive_surface(self):
        # documented contract: vocab entries are strings, fields closed
        assert all(isinstance(v, str) for v in VOCABULARY)
        assert "tempo_philosophy" in FIELDS


class TestIdentityGuard:
    def test_artist_identity_requires_license(self):
        with pytest.raises(PhilosophyError, match="Glenn Gould"):
            phil({"tempo_philosophy": ["in the manner of Glenn Gould"]})

    def test_artist_identity_with_license_accepted(self):
        prov = {"author": "founder", "ai_assisted": False,
                "license_ref": "estate-agreement-2026-001"}
        phil({"tempo_philosophy": ["in the manner of Glenn Gould"]}, prov=prov)

    def test_composer_identity_requires_license(self):
        with pytest.raises(PhilosophyError, match="Johann Sebastian Bach"):
            phil({"articulation_stance": ["as Johann Sebastian Bach intended"]})

    def test_era_phrases_are_not_identities(self):
        phil({"tempo_philosophy": ["Viennese Classical restraint"]})
        phil({"ensemble_stance": ["Venetian School antiphony"]})

    def test_styles_and_practices_free(self):
        phil({"dynamic_philosophy": ["baroque terracing, messa di voce swells"]})


class TestProvenance:
    def test_author_required(self):
        with pytest.raises(PhilosophyError, match="author"):
            phil({"tempo_philosophy": ["strict"]},
                 prov={"ai_assisted": False})

    def test_ai_disclosure_required(self):
        with pytest.raises(PhilosophyError, match="ai_assisted"):
            phil({"tempo_philosophy": ["strict"]}, prov={"author": "founder"})

    def test_ai_disclosure_must_be_boolean(self):
        with pytest.raises(PhilosophyError, match="boolean"):
            phil({"tempo_philosophy": ["strict"]},
                 prov={"author": "founder", "ai_assisted": "yes"})

    def test_ai_assisted_true_accepted(self):
        phil({"tempo_philosophy": ["strict"]},
             prov={"author": "founder", "ai_assisted": True})


class TestRoundTrip:
    def test_dict_round_trip(self):
        p = phil({"tempo_philosophy": ["flexible"],
                  "articulation_stance": ["consort", "breathe-at-cadences"]})
        q = Philosophy.from_dict(p.to_dict())
        assert q.entries == p.entries
        assert q.provenance == p.provenance


class TestSeedIntegration:
    def make_seed(self, philosophy):
        return Seed(format_version="0.1", work_id="bach-bwv227",
                    params={"tempo": {"min_bpm": 60, "max_bpm": 120, "default_bpm": 96}},
                    philosophy=philosophy,
                    assertions={"must_contain": ["theme"]})

    def test_valid_philosophy_passes_seed_validation(self):
        seed = self.make_seed({
            "tempo_philosophy": ["flexible", "architectural"],
            "provenance": {"author": "founder", "ai_assisted": False},
        })
        validate_seed(seed)

    def test_bad_philosophy_fails_seed_validation(self):
        seed = self.make_seed({"tempo_philosophy": ["in the manner of Glenn Gould"],
                               "provenance": {"author": "founder", "ai_assisted": False}})
        with pytest.raises(SeedError, match="Glenn Gould"):
            validate_seed(seed)

    def test_empty_philosophy_is_optional(self):
        seed = self.make_seed({})
        validate_seed(seed)  # philosophy block may be absent
