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


# --- S5.1 lineage fields (issue #256; spec
# tests/open_20260826-000500_s5-1-manifest-lineage.md) ---

from muse_mu.manifest import is_sha256_hex  # noqa: E402

GOOD_HASH = "a" * 64


class TestLineageFields:
    """provenance.extends (bare 64-hex) + provenance.operation (string),
    both optional (S5.1, #249)."""

    def test_no_lineage_fields_valid(self):
        make_manifest().validate()

    def test_extends_only_valid(self):
        make_manifest(provenance=dict(PROVENANCE, extends=GOOD_HASH)).validate()

    def test_operation_only_valid(self):
        make_manifest(provenance=dict(PROVENANCE, operation="muse_distill@1")).validate()

    def test_both_round_trip_through_dict(self):
        prov = dict(PROVENANCE, extends=GOOD_HASH, operation="muse_author@1.2.3")
        m = make_manifest(provenance=prov)
        m2 = Manifest.from_json(m.to_json())
        assert m2.provenance["extends"] == GOOD_HASH
        assert m2.provenance["operation"] == "muse_author@1.2.3"

    @pytest.mark.parametrize("bad", [
        "a" * 63, "a" * 65, "g" * 64, "sha256:" + GOOD_HASH, 123, [GOOD_HASH],
    ])
    def test_extends_rejected(self, bad):
        with pytest.raises(ManifestError, match="extends"):
            make_manifest(provenance=dict(PROVENANCE, extends=bad)).validate()

    @pytest.mark.parametrize("bad", [42, ["muse_distill@1"]])
    def test_operation_non_string_rejected(self, bad):
        with pytest.raises(ManifestError, match="operation"):
            make_manifest(provenance=dict(PROVENANCE, operation=bad)).validate()

    def test_unknown_key_guard_unchanged(self):
        """The frozenset grew by exactly two keys; anything else still fails."""
        with pytest.raises(ManifestError, match="unknown provenance keys"):
            make_manifest(provenance=dict(PROVENANCE, bogus_key="x")).validate()

    def test_sha256_hex_parity(self):
        """The extends check and the member-hash check share one
        implementation — accept/reject identically across the matrix
        (the extraction regression pin)."""
        matrix = [GOOD_HASH, GOOD_HASH.upper(), "a" * 63, "a" * 65,
                  "g" * 64, "sha256:" + GOOD_HASH, "", 123, []]
        for value in matrix:
            expect = is_sha256_hex(value)
            try:
                m = make_manifest()
                m.hashes["roll.bin"] = value
                m._validate_hashes()
                member_ok = True
            except ManifestError:
                member_ok = False
            try:
                make_manifest(provenance=dict(PROVENANCE, extends=value)).validate()
                ext_ok = True
            except ManifestError:
                ext_ok = False
            assert member_ok == expect, f"member-hash parity broke on {value!r}"
            assert ext_ok == expect, f"extends parity broke on {value!r}"

    def test_container_seam_round_trip_and_tamper(self, tmp_path):
        """write_mu/read_mu preserve the lineage fields. Note on the
        tamper surface (spec item 6, corrected): manifest.json is never
        hashed by design (the manifest never hashes itself), so a repacked
        manifest alone does NOT trip the hash gate — what it trips is the
        HMAC verify when signed. The member-hash gate catches tampering
        with member *content*."""
        prov = dict(PROVENANCE, extends=GOOD_HASH, operation="muse_distill@1")
        m = make_manifest(provenance=prov)
        mu = tmp_path / "t.mu"
        write_mu(str(mu), m, MEMBERS)
        back, _members = read_mu(str(mu))
        assert back.provenance["extends"] == GOOD_HASH
        assert back.provenance["operation"] == "muse_distill@1"

        # member tamper (the surface the hash gate actually covers)
        with zipfile.ZipFile(mu) as z:
            members = {n: z.read(n) for n in z.namelist()}
        members["roll.bin"] = b"tampered"
        with zipfile.ZipFile(mu, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in members.items():
                z.writestr(name, data)
        with pytest.raises(ManifestError, match="hash mismatch"):
            read_mu(str(mu))

    def test_signed_manifest_tamper_fails_verify(self, tmp_path):
        """The manifest-side tamper surface: a repacked manifest.json with
        a forged extends invalidates the signature."""
        prov = dict(PROVENANCE, extends=GOOD_HASH)
        m = make_manifest(provenance=prov)
        m.sign(b"k")
        mu = tmp_path / "s.mu"
        write_mu(str(mu), m, MEMBERS)
        with zipfile.ZipFile(mu) as z:
            members = {n: z.read(n) for n in z.namelist()}
        doc = json.loads(members["manifest.json"])
        doc["provenance"]["extends"] = "b" * 64
        members["manifest.json"] = json.dumps(doc, indent=2).encode()
        with zipfile.ZipFile(mu, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in members.items():
                z.writestr(name, data)
        back, _ = read_mu(str(mu))
        assert not back.verify(b"k")
