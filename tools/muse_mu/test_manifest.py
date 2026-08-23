"""S5 container + manifest tests (issue #141).

Manifest schema (license enum, provenance + AI disclosure, hashes),
container layout (required members, optional performances/), hash
verification, and the HMAC signature.
"""

import json
import zipfile

import pytest

from muse_mu import (
    Manifest,
    ManifestError,
    build_manifest,
    read_mu,
    sha256_hex,
    write_mu,
)

LICENSE = {"renditions": "open-within-constraints",
           "attribution": "J.S. Bach (1685–1750), public domain",
           "commercial": False}
PROVENANCE = {"source": "corpus/bach/bwv227.1.mxl",
              "author": "founder",
              "ai_involvement": "assisted",
              "tools": ["tools/ir", "tools/muse_seed"]}
MEMBERS = {"roll.bin": b"fake-roll-bytes", "seed.bin": b"fake-seed-bytes"}


def make_manifest(**kw):
    args = dict(work_id="bwv227.1", license=dict(LICENSE),
                provenance=dict(PROVENANCE), members=dict(MEMBERS),
                title="Jesu, meine Freude", composer="Johann Sebastian Bach")
    args.update(kw)
    return build_manifest(**args)


class TestManifestSchema:
    def test_valid_manifest(self):
        make_manifest().validate()

    @pytest.mark.parametrize("renditions", ["presets-only", "open-within-constraints", "closed"])
    def test_license_enum(self, renditions):
        make_manifest(license={**LICENSE, "renditions": renditions})

    def test_bad_renditions_rejected(self):
        with pytest.raises(ManifestError, match="renditions"):
            make_manifest(license={**LICENSE, "renditions": "whatever"})

    def test_attribution_required(self):
        with pytest.raises(ManifestError, match="attribution"):
            make_manifest(license={**LICENSE, "attribution": ""})

    def test_commercial_must_be_boolean(self):
        with pytest.raises(ManifestError, match="commercial"):
            make_manifest(license={**LICENSE, "commercial": "no"})

    def test_ai_disclosure_mandatory(self):
        with pytest.raises(ManifestError, match="ai_involvement"):
            make_manifest(provenance={k: v for k, v in PROVENANCE.items()
                                      if k != "ai_involvement"})

    @pytest.mark.parametrize("ai", ["none", "assisted", "generated"])
    def test_ai_disclosure_values(self, ai):
        make_manifest(provenance={**PROVENANCE, "ai_involvement": ai})

    def test_unknown_keys_rejected(self):
        m = make_manifest()
        d = m.to_dict()
        d["vibe"] = "good"
        with pytest.raises(ManifestError, match="unknown manifest keys"):
            Manifest.from_dict(d)

    def test_manifest_must_not_hash_itself(self):
        with pytest.raises(ManifestError, match="must not hash itself"):
            make_manifest(members={**MEMBERS, "manifest.json": b"x"})

    def test_json_round_trip(self):
        m = make_manifest()
        assert Manifest.from_json(m.to_json()).to_dict() == m.to_dict()

    def test_human_readable_plaintext(self):
        text = make_manifest().to_json()
        parsed = json.loads(text)  # a lawyer's text editor: plain JSON
        assert parsed["license"]["renditions"] == "open-within-constraints"
        assert parsed["provenance"]["ai_involvement"] == "assisted"


class TestContainer:
    def test_write_read_round_trip(self, tmp_path):
        path = str(tmp_path / "work.mu")
        write_mu(path, make_manifest(), MEMBERS)
        manifest, members = read_mu(path)
        assert manifest.work_id == "bwv227.1"
        assert members == MEMBERS

    def test_performances_dir_accepted(self, tmp_path):
        members = {**MEMBERS, "performances/a.perf": b"perf-bytes"}
        path = str(tmp_path / "work.mu")
        write_mu(path, make_manifest(members=members), members)
        _, got = read_mu(path)
        assert got["performances/a.perf"] == b"perf-bytes"

    def test_missing_required_member_rejected(self, tmp_path):
        path = str(tmp_path / "work.mu")
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("manifest.json", make_manifest().to_json())
            z.writestr("roll.bin", b"x")
        with pytest.raises(ManifestError, match="seed.bin"):
            read_mu(path)

    def test_unexpected_member_rejected(self, tmp_path):
        path = str(tmp_path / "work.mu")
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("manifest.json", make_manifest().to_json())
            z.writestr("roll.bin", MEMBERS["roll.bin"])
            z.writestr("seed.bin", MEMBERS["seed.bin"])
            z.writestr("readme.txt", b"surprise")
        with pytest.raises(ManifestError, match="unexpected member"):
            read_mu(path)

    def test_not_a_zip_rejected(self, tmp_path):
        path = tmp_path / "work.mu"
        path.write_bytes(b"definitely not a zip")
        with pytest.raises(ManifestError, match="not a .mu zip"):
            read_mu(str(path))

    def test_hash_mismatch_detected(self, tmp_path):
        # a zip whose roll.bin content differs from the manifest's hash
        path = str(tmp_path / "work.mu")
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("manifest.json", make_manifest().to_json())
            z.writestr("roll.bin", b"tampered-content")
            z.writestr("seed.bin", MEMBERS["seed.bin"])
        with pytest.raises(ManifestError, match="hash mismatch"):
            read_mu(path)

    def test_write_rejects_hash_mismatch(self, tmp_path):
        m = make_manifest()
        with pytest.raises(ManifestError, match="do not match"):
            write_mu(str(tmp_path / "w.mu"), m, {"roll.bin": b"different",
                                                 "seed.bin": MEMBERS["seed.bin"]})


class TestSignature:
    KEY = b"test-signing-key"

    def test_sign_and_verify(self):
        m = make_manifest()
        m.sign(self.KEY)
        assert m.verify(self.KEY)

    def test_wrong_key_fails(self):
        m = make_manifest()
        m.sign(self.KEY)
        assert not m.verify(b"other-key")

    def test_tampered_manifest_fails_verify(self):
        m = make_manifest()
        m.sign(self.KEY)
        m.title = "forged title"
        assert not m.verify(self.KEY)

    def test_unsigned_verify_raises(self):
        with pytest.raises(ManifestError, match="no signature"):
            make_manifest().verify(self.KEY)

    def test_signature_survives_json_round_trip(self):
        m = make_manifest()
        m.sign(self.KEY)
        assert Manifest.from_json(m.to_json()).verify(self.KEY)


def test_sha256_hex():
    assert sha256_hex(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
