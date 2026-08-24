"""P1 reference decoder tests (spec: tests/open_20260824-020000_p1-decoder.md).

Container decode round-trips and every failure path the spec lists:
missing container, bad zip, missing manifest or roll member.
"""

import os
import sys
import zipfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_decode import DecodeError, decode  # noqa: E402
from muse_ir import load  # noqa: E402
from muse_mu import build_manifest, write_mu  # noqa: E402
from muse_roll import encode  # noqa: E402
from muse_roll.roll import _canonical  # noqa: E402

CORPUS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "corpus"))
SEED_YAML = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "seeds",
                                          "bwv227.1.seed.yaml"))

TIERS = ["bach/bwv227.1.mxl", "byrd/1-Kyrie.mid"]


def _build_container(tmp_path, relpath, work_id="t"):
    """Source → S2 pack → S5 container on disk; returns the path."""
    work = load(os.path.join(CORPUS, relpath))
    with open(SEED_YAML, "rb") as fh:
        seed = fh.read()
    members = {"roll.bin": encode(work), "seed.bin": seed}
    manifest = build_manifest(
        work_id=work_id,
        license={"renditions": "closed", "attribution": "tests", "commercial": False},
        provenance={"source": relpath, "author": "tests", "ai_involvement": "none"},
        members=members)
    path = str(tmp_path / f"{work_id}.mu")
    write_mu(path, manifest, members)
    return path, work


class TestContainerDecode:
    @pytest.mark.parametrize("relpath", TIERS)
    def test_container_decode_matches_original(self, relpath, tmp_path):
        path, work = _build_container(tmp_path, relpath)
        out = decode(path)
        assert len(out.parts) == len(work.parts)
        assert out.note_count == work.note_count

    def test_round_trip_exact(self, tmp_path):
        """pack → container → decode → canonical-exact original (both parse
        paths: MusicXML and MIDI)."""
        for relpath in TIERS:
            path, work = _build_container(tmp_path, relpath)
            assert _canonical(decode(path)) == _canonical(work), relpath


class TestFailurePaths:
    def test_missing_container(self, tmp_path):
        with pytest.raises(DecodeError, match="container not found"):
            decode(str(tmp_path / "absent.mu"))

    def test_bad_zip(self, tmp_path):
        bad = tmp_path / "bad.mu"
        bad.write_bytes(b"not a zip container")
        with pytest.raises(DecodeError, match="bad zip container"):
            decode(str(bad))

    def test_missing_manifest_member(self, tmp_path):
        path = tmp_path / "no-manifest.mu"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("roll.bin", b"x")
        with pytest.raises(DecodeError, match="manifest.json or roll.bin"):
            decode(str(path))

    def test_missing_roll_member(self, tmp_path):
        path = tmp_path / "no-roll.mu"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("manifest.json", b"{}")
        with pytest.raises(DecodeError, match="manifest.json or roll.bin"):
            decode(str(path))

    def test_corrupt_roll_payload_loud(self, tmp_path):
        """A well-formed container whose roll.bin is corrupt must raise
        DecodeError, not return partial data."""
        path, _ = _build_container(tmp_path, TIERS[0])
        with zipfile.ZipFile(path) as z:
            members = {n: z.read(n) for n in z.namelist()}
        members["roll.bin"] = b"\x00" * 16
        with zipfile.ZipFile(path, "a") as z:
            z.writestr("roll.bin", members["roll.bin"])
        with pytest.raises(DecodeError, match="roll decode failed"):
            decode(str(path))
