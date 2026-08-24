"""Tests: P1 reference decoder (#202). Spec: tests/open_20260824-020000_p1-decoder.md."""

import os
import sys
import json
import zipfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from muse_ir import load  # noqa: E402
from muse_roll import encode  # noqa: E402
from muse_decode import decode, DecodeError  # noqa: E402
from muse_decode.cli import main as cli_main  # noqa: E402

CORPUS = os.path.join(os.path.dirname(__file__), "..", "..", "corpus")


def _build_container(work_rel, container_path):
    w = load(os.path.join(CORPUS, work_rel))
    pack_bytes = encode(w)
    manifest = {
        "format_version": "0.1",
        "work_id": "test",
        "title": "test",
        "license": "presets-only",
        "provenance": {"author": "test", "ai_assisted": False, "source_format": "musicxml"},
    }
    with zipfile.ZipFile(container_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("roll.bin", pack_bytes)
        zf.writestr("performances/", "")
    return w


def _read_container(container_path):
    with zipfile.ZipFile(container_path) as zf:
        return zf.read("manifest.json"), zf.read("roll.bin")


class TestContainerDecode:
    def test_roundtrip_bach(self, tmp_path):
        original = _build_container("bach/bwv227.1.mxl", str(tmp_path / "t.mu"))
        decoded = decode(str(tmp_path / "t.mu"))
        assert len(decoded.parts) == len(original.parts)
        assert decoded.note_count == original.note_count

    def test_roundtrip_byrd(self, tmp_path):
        original = _build_container("byrd/1-Kyrie.mid", str(tmp_path / "t.mu"))
        decoded = decode(str(tmp_path / "t.mu"))
        assert len(decoded.parts) == len(original.parts)
        assert decoded.note_count == original.note_count

    def test_missing_container(self, tmp_path):
        with pytest.raises(DecodeError, match="not found"):
            decode(str(tmp_path / "missing.mu"))

    def test_bad_zip(self, tmp_path):
        bad = tmp_path / "bad.mu"
        bad.write_text("not a zip")
        with pytest.raises(DecodeError, match="bad zip"):
            decode(str(bad))

    def test_missing_manifest(self, tmp_path):
        bad = tmp_path / "bad.mu"
        with zipfile.ZipFile(str(bad), "w") as zf:
            zf.writestr("roll.bin", b"x")
        with pytest.raises(DecodeError, match="missing manifest"):
            decode(str(bad))

    def test_missing_roll(self, tmp_path):
        bad = tmp_path / "bad.mu"
        with zipfile.ZipFile(str(bad), "w") as zf:
            zf.writestr("manifest.json", b"{}")
        with pytest.raises(DecodeError, match="missing manifest"):
            decode(str(bad))


class TestCLI:
    def test_cli_exit_zero_on_valid(self, tmp_path):
        container = tmp_path / "t.mu"
        _build_container("bach/bwv227.1.mxl", str(container))
        rc = cli_main([str(container)])
        assert rc == 0

    def test_cli_exit_one_on_invalid(self, tmp_path):
        bad = tmp_path / "bad.mu"
        bad.write_text("not a zip")
        rc = cli_main([str(bad)])
        assert rc == 1


class TestContainerIntegrity:
    def test_container_roundtrip_bytes(self, tmp_path):
        container = tmp_path / "t.mu"
        _build_container("bach/bwv227.1.mxl", str(container))
        manifest, roll = _read_container(str(container))
        assert json.loads(manifest) is not None
        assert len(roll) > 0

    def test_decoder_determinism(self, tmp_path):
        container = tmp_path / "t.mu"
        _build_container("bach/bwv227.1.mxl", str(container))
        d1 = decode(str(container))
        d2 = decode(str(container))
        assert d1.note_count == d2.note_count
        assert [p.id for p in d1.parts] == [p.id for p in d2.parts]
