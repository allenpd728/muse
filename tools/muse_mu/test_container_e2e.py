"""Tests: S5 follow-up (issue #152).

1. Golden .mu fixture — committed bytes, verified byte-exact.
2. Signature canonicalization adversarial cases.
3. Zip metadata edge cases (duplicate members, directory entries).
4. Real-payload shape: .mu built from an actual seed file + corpus-derived bytes.
"""

import json
import os
import sys
import zipfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_mu import (  # noqa: E402
    Manifest,
    ManifestError,
    build_manifest,
    read_mu,
    sha256_hex,
    write_mu,
)

FIXTURES = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "tests", "fixtures"))
GOLDEN = os.path.join(FIXTURES, "bwv227.1.minimal.mu")
SEED_YAML = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "seeds", "bwv227.1.seed.yaml"))

LICENSE = {"renditions": "open-within-constraints",
           "attribution": "J.S. Bach (1685–1750), public domain",
           "commercial": False}
PROVENANCE = {"source": "corpus/bach/bwv227.1.mxl", "author": "founder",
              "ai_involvement": "assisted"}
MEMBERS = {"roll.bin": b"MUSE-ROLL-V0", "seed.bin": b"MUSE-SEED-V0"}
KEY = b"s5-golden-key"

# Canonical inputs of the committed golden fixture. Rebuilds must match.
FIXTURE_INPUTS = dict(
    work_id="bwv227.1",
    title="Jesu, meine Freude",
    composer="Johann Sebastian Bach",
    license=LICENSE,
    provenance={"source": "corpus/bach/bwv227.1.mxl", "author": "founder",
                "ai_involvement": "assisted",
                "tools": ["tools/ir", "tools/muse_seed"]},
    members=MEMBERS,
)


def make_manifest(members=MEMBERS, **kw):
    args = dict(work_id="bwv227.1", license=dict(LICENSE),
                provenance=dict(PROVENANCE), members=dict(members))
    args.update(kw)
    return build_manifest(**args)


class TestGoldenFixture:
    def test_fixture_verifies_byte_exact(self):
        manifest, members = read_mu(GOLDEN)
        assert manifest.work_id == "bwv227.1"
        assert manifest.title == "Jesu, meine Freude"
        assert members == {"roll.bin": b"MUSE-ROLL-V0", "seed.bin": b"MUSE-SEED-V0"}

    def test_fixture_is_reproducible(self, tmp_path):
        # Rebuilding from FIXTURE_INPUTS yields identical members and an
        # identical manifest (zip timestamps may differ — compare payloads).
        out = str(tmp_path / "re.mu")
        write_mu(out, build_manifest(**FIXTURE_INPUTS), MEMBERS)
        _, members_a = read_mu(GOLDEN)
        _, members_b = read_mu(out)
        assert members_a == members_b
        with zipfile.ZipFile(GOLDEN) as z:
            manifest_a = z.read("manifest.json")
        with zipfile.ZipFile(out) as z:
            manifest_b = z.read("manifest.json")
        assert manifest_a == manifest_b


class TestCanonicalization:
    def test_unicode_title_sign_verify(self):
        m = make_manifest(title="Jésu, meine Freude — BWV 227")
        m.sign(KEY)
        assert m.verify(KEY)
        assert Manifest.from_json(m.to_json()).verify(KEY)

    def test_nested_dict_order_is_canonical(self):
        m = make_manifest()
        m.sign(KEY)
        # same content, different dict insertion order → same signature
        prov = {"ai_involvement": "assisted", "author": "founder",
                "source": "corpus/bach/bwv227.1.mxl"}
        m2 = build_manifest(work_id="bwv227.1", license=dict(LICENSE),
                            provenance=prov, members=dict(MEMBERS))
        m2.sign(KEY)
        assert m.signature == m2.signature

    def test_whitespace_in_attribution_changes_signature(self):
        m = make_manifest()
        m.sign(KEY)
        m2 = build_manifest(work_id="bwv227.1",
                            license={**LICENSE, "attribution": LICENSE["attribution"] + " "},
                            provenance=dict(PROVENANCE), members=dict(MEMBERS))
        m2.sign(KEY)
        assert m.signature != m2.signature


class TestZipMetadata:
    def test_duplicate_member_names_loud(self, tmp_path):
        # Decision pinned: duplicate member names = corrupt container,
        # fail loudly (zipfile.read would silently return the last entry).
        path = str(tmp_path / "dup.mu")
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("manifest.json", make_manifest().to_json())
            z.writestr("roll.bin", b"first")
            z.writestr("roll.bin", b"second")   # duplicate name
            z.writestr("seed.bin", MEMBERS["seed.bin"])
        with pytest.raises(ManifestError, match="duplicate members"):
            read_mu(path)

    def test_directory_entry_noise_accepted(self, tmp_path):
        # tools that write explicit dir entries (e.g. "performances/")
        # must not trip the unexpected-member rule when empty
        path = str(tmp_path / "dir.mu")
        members = {**MEMBERS, "performances/a.perf": b"x"}
        write_mu(path, make_manifest(members=members), members)
        with zipfile.ZipFile(path, "a") as z:
            z.writestr("performances/", b"")     # explicit dir entry
        manifest, got = read_mu(path)
        assert got["performances/a.perf"] == b"x"


class TestRealPayloadShape:
    def test_mu_from_real_seed_and_corpus_bytes(self, tmp_path):
        roll = open(os.path.join(FIXTURES, "..", "..", "corpus", "bach", "bwv227.1.mxl"), "rb").read()
        seed = open(SEED_YAML, "rb").read()
        members = {"roll.bin": roll, "seed.bin": seed}
        m = make_manifest(members=members)
        path = str(tmp_path / "real.mu")
        write_mu(path, m, members)
        manifest, got = read_mu(path)
        assert sha256_hex(got["roll.bin"]) == sha256_hex(roll)
        assert manifest.hashes["seed.bin"] == sha256_hex(seed)
