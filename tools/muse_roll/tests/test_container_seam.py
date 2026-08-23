"""S2 ↔ S5 seam tests (issue #165).

The pack→container seam was untested: S2's tests never wrote a container
and S5's tests used raw bytes, not packed payloads. This suite covers both
directions of the contract:

- **S2 → S5**: an S2-packed roll payload writes into a .mu container as
  ``roll.bin``; the manifest's sha256 of ``roll.bin`` equals the packed
  payload's digest at build time and after read-back.
- **S5 → S2**: ``read_mu`` returns the payload byte-exact; S2 decodes it;
  W4 diff against the source IR is green (recall = precision = 1.0) on
  three corpus tiers (Bach mxl, Byrd mid, Schubert mxl).
- **Corruption**: a tampered ``roll.bin`` fails loudly at container read
  (manifest hash mismatch) and, if re-hashed to hide the tamper, fails
  loudly at decode — never silent partial data.

``seed.bin`` is a required S5 member but not the seam under test; the real
Bach seed yaml stands in as its bytes.
"""

import os
import sys
import zipfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "muse_diff"))

from muse_ir import load  # noqa: E402
from muse_diff import diff  # noqa: E402
from muse_mu import (  # noqa: E402
    ManifestError,
    build_manifest,
    read_mu,
    sha256_hex,
    write_mu,
)
from muse_roll import decode, encode  # noqa: E402
from muse_roll.roll import MAGIC, RollError  # noqa: E402

HERE = os.path.dirname(__file__)
CORPUS = os.path.normpath(os.path.join(HERE, "..", "..", "..", "corpus"))
SEED_YAML = os.path.normpath(os.path.join(HERE, "..", "..", "..", "seeds",
                                          "bwv227.1.seed.yaml"))

# Corpus tiers (the ladder's first three rungs — two distinct parse paths:
# MusicXML and MIDI).
TIERS = {
    "bach": "bach/bwv227.1.mxl",
    "byrd": "byrd/1-Kyrie.mid",
    "schubert": "schubert/death-and-the-maiden.mxl",
}

LICENSE = {"renditions": "open-within-constraints",
           "attribution": "corpus reference works, public domain",
           "commercial": False}


def _seed_bytes():
    with open(SEED_YAML, "rb") as f:
        return f.read()


def _pack_into_container(work, work_id, source, path):
    """S2 pack → S5 write. Returns (packed_payload, written_manifest)."""
    payload = encode(work)
    members = {"roll.bin": payload, "seed.bin": _seed_bytes()}
    manifest = build_manifest(
        work_id=work_id,
        license=dict(LICENSE),
        provenance={"source": source, "author": "founder",
                    "ai_involvement": "none",
                    "tools": ["tools/ir", "tools/muse_roll", "tools/muse_mu"]},
        members=members,
    )
    write_mu(str(path), manifest, members)
    return payload, manifest


def _replace_member(path, member, data):
    """Rewrite the zip with one member's bytes replaced (manifest kept)."""
    with zipfile.ZipFile(path) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    contents[member] = data
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, payload in contents.items():
            z.writestr(name, payload)


class TestPackContainerUnpackRoundTrip:
    @pytest.mark.parametrize("tier", sorted(TIERS))
    def test_container_roundtrip_w4_green(self, tier, tmp_path):
        work = load(os.path.join(CORPUS, TIERS[tier]))
        path = tmp_path / f"{tier}.mu"
        payload, _ = _pack_into_container(work, tier, TIERS[tier], path)

        manifest, members = read_mu(str(path))
        assert members["roll.bin"] == payload, f"{tier}: payload not byte-exact through container"
        assert manifest.hashes["roll.bin"] == sha256_hex(payload)

        restored = decode(members["roll.bin"])
        report = diff(work, restored)
        assert report.ok(), (
            f"{tier}: W4 diff not clean after container round-trip: "
            f"recall={report.recall:.4f} precision={report.precision:.4f} "
            f"({[m.describe() for m in report.mismatches[:5]]})"
        )


class TestManifestHashPinsPayload:
    def test_roll_bin_hash_matches_packed_payload(self, tmp_path):
        """The manifest hash of roll.bin is the packed payload's sha256 —
        at build time and as read back from the container."""
        work = load(os.path.join(CORPUS, TIERS["bach"]))
        path = tmp_path / "hash.mu"
        payload, written = _pack_into_container(work, "bach", TIERS["bach"], path)

        assert written.hashes["roll.bin"] == sha256_hex(payload)
        manifest, members = read_mu(str(path))
        assert manifest.hashes["roll.bin"] == sha256_hex(payload)
        assert manifest.hashes["roll.bin"] == sha256_hex(members["roll.bin"])

    def test_roll_bin_hash_pinned_to_golden_fixture(self, tmp_path):
        """T2's golden roll vector and the container agree on the digest."""
        fixture = os.path.normpath(os.path.join(
            HERE, "..", "..", "..", "tests", "fixtures", "bwv227.1.roll.bin"))
        if not os.path.exists(fixture):
            pytest.skip("golden roll fixture not committed")
        with open(fixture, "rb") as f:
            golden = f.read()
        work = load(os.path.join(CORPUS, TIERS["bach"]))
        path = tmp_path / "golden.mu"
        payload, _ = _pack_into_container(work, "bach", TIERS["bach"], path)
        assert payload == golden, "packed payload drifted from golden roll vector"
        manifest, _ = read_mu(str(path))
        assert manifest.hashes["roll.bin"] == sha256_hex(golden)


class TestCorruptionFailsLoudly:
    def test_tampered_roll_member_hash_mismatch(self, tmp_path):
        """Flip a byte in roll.bin (manifest untouched): read_mu must raise
        on the hash mismatch — no silent partial data."""
        work = load(os.path.join(CORPUS, TIERS["bach"]))
        path = tmp_path / "tampered.mu"
        payload, _ = _pack_into_container(work, "bach", TIERS["bach"], path)

        tampered = payload[:-1] + bytes([payload[-1] ^ 0xFF])
        _replace_member(path, "roll.bin", tampered)
        with pytest.raises(ManifestError, match="hash mismatch"):
            read_mu(str(path))

    def test_rehashed_tamper_fails_at_decode(self, tmp_path):
        """Tamper hidden by re-hashing (corrupt MAGIC, honest manifest):
        container read passes, but S2 decode must raise, not return a
        partial/garbage Work."""
        work = load(os.path.join(CORPUS, TIERS["bach"]))
        path = tmp_path / "rehashed.mu"
        payload, _ = _pack_into_container(work, "bach", TIERS["bach"], path)

        corrupted = b"XXXX" + payload[4:]
        assert corrupted[:4] != MAGIC
        members = {"roll.bin": corrupted, "seed.bin": _seed_bytes()}
        manifest = build_manifest(work_id="bach", license=dict(LICENSE),
                                  provenance={"source": TIERS["bach"],
                                              "author": "founder",
                                              "ai_involvement": "none"},
                                  members=members)
        write_mu(str(path), manifest, members)

        _, got = read_mu(str(path))  # hashes honest → read succeeds
        with pytest.raises(RollError):
            decode(got["roll.bin"])

    def test_missing_roll_member_loud(self, tmp_path):
        """A container whose roll.bin was stripped fails at read, listing
        the required member — the unpack stage never sees partial data."""
        work = load(os.path.join(CORPUS, TIERS["bach"]))
        path = tmp_path / "stripped.mu"
        _pack_into_container(work, "bach", TIERS["bach"], path)

        with zipfile.ZipFile(path) as z:
            contents = {n: z.read(n) for n in z.namelist() if n != "roll.bin"}
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, payload in contents.items():
                z.writestr(name, payload)
        with pytest.raises(ManifestError, match="required member 'roll.bin' missing"):
            read_mu(str(path), verify_hashes=False)
