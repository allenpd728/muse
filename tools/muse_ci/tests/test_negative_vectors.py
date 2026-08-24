"""P3 negative-vector tier (issue #231, spec follow-up): deliberately
malformed .mu inputs with pinned DecodeError classes.

The positive store proves good vectors decode to pinned bytes; this tier
pins the *failure* surface — a conformance gate that can't name its error
classes lets a decoder drift its contract silently. Vectors are derived
from the committed positive vector by controlled corruption (provenance
stays reviewable; no opaque binaries committed), and each is pinned to
its DecodeError class + message fragment, then proven to FAIL the gate —
never pass, never raise.
"""

import os
import re
import shutil
import zipfile

import pytest

from muse_decode import DecodeError, decode

from muse_ci import PINS_NAME, VECTORS_DIR, verify
from muse_ci.cli import main as cli_main

POSITIVE = os.path.join(VECTORS_DIR, "bach-bwv227.1.mu")
WORK_ID = "bach-bwv227.1"
RELPATH = "bach/bwv227.1.mxl"


def _members(path):
    with zipfile.ZipFile(path) as zf:
        return {n: zf.read(n) for n in zf.namelist()}


def _write_mu(path, members):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)


def make_not_a_zip(path):
    path.write_bytes(b"MUR1 but not actually a zip container at all")


def make_missing_manifest(path):
    members = _members(POSITIVE)
    del members["manifest.json"]
    _write_mu(path, members)


def make_missing_roll(path):
    members = _members(POSITIVE)
    del members["roll.bin"]
    _write_mu(path, members)


def make_corrupt_roll(path):
    members = _members(POSITIVE)
    members["roll.bin"] = b"\x00" * 64
    _write_mu(path, members)


# name → (builder, pinned DecodeError message fragment)
NEGATIVE_VECTORS = {
    "not-a-zip": (make_not_a_zip, "bad zip container"),
    "missing-manifest": (make_missing_manifest, "missing manifest.json or roll.bin"),
    "missing-roll": (make_missing_roll, "missing manifest.json or roll.bin"),
    "corrupt-roll": (make_corrupt_roll, "roll decode failed"),
}


@pytest.fixture(params=sorted(NEGATIVE_VECTORS), ids=sorted(NEGATIVE_VECTORS))
def negative_mu(request, tmp_path):
    build, pinned_fragment = NEGATIVE_VECTORS[request.param]
    mu = tmp_path / f"{request.param}.mu"
    build(mu)
    return request.param, mu, pinned_fragment


class TestPinnedDecodeErrors:
    def test_decode_raises_pinned_error(self, negative_mu):
        name, mu, fragment = negative_mu
        with pytest.raises(DecodeError, match=re.escape(fragment)):
            decode(str(mu))

    def test_error_class_is_stable(self, negative_mu):
        """The pinned class is DecodeError itself — a regression to a bare
        zipfile/ValueError leak would break the P1 contract's callers."""
        name, mu, _ = negative_mu
        with pytest.raises(DecodeError):
            decode(str(mu))
        try:
            decode(str(mu))
        except DecodeError:
            pass
        else:
            raise AssertionError(f"{name} decoded without error")


class TestNegativeVectorsFailTheGate:
    """Each negative vector, swapped into a store copy, must FAIL verify —
    never pass, never raise."""

    def _tampered_store(self, tmp_path, mu):
        store = tmp_path / "vectors"
        store.mkdir()
        shutil.copy(os.path.join(VECTORS_DIR, PINS_NAME), store / PINS_NAME)
        shutil.copy(mu, store / f"{WORK_ID}.mu")
        return store

    def test_verify_fails_without_raising(self, negative_mu, tmp_path):
        name, mu, fragment = negative_mu
        store = self._tampered_store(tmp_path, mu)
        (r,) = verify(str(store), registry=[(WORK_ID, RELPATH)])
        assert r.status == "FAIL"
        assert r.detail, f"{name}: FAIL must name a reason"

    def test_cli_exits_1_on_negative_vector(self, negative_mu, tmp_path, capsys):
        name, mu, _ = negative_mu
        store = self._tampered_store(tmp_path, mu)
        rc = cli_main(["verify", "--vectors", str(store)])
        assert rc == 1
        out = capsys.readouterr().out
        assert "FAIL" in out


def test_negative_tier_is_exhaustive_over_builder_table():
    """The builder table is the tier's registry — a new malformed class
    belongs here, pinned, not inline in a one-off test."""
    assert len(NEGATIVE_VECTORS) >= 4
    assert all(callable(b) and f for b, f in NEGATIVE_VECTORS.values())
