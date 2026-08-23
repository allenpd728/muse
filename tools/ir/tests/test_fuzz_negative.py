"""Negative-path corpus sweep (spec gap 6).

Malformed-input tests elsewhere are synthetic; here we fuzz real corpus
files: every truncated/corrupted variant must surface as IRParseError —
never a hang, never a partial Work.
"""

import io
import os
import random
import zipfile

import pytest

from conftest import CORPUS_ROOT, corpus_path

from muse_ir import IRParseError, load

CORPUS_FILES = [
    ("bach", "bwv227.1.mxl"),
    ("bach", "bwv227.3.mxl"),
    ("bach", "bwv227.7.mxl"),
    ("bach", "bwv227.11.mxl"),
    ("byrd", "1-Kyrie.mid"),
    ("byrd", "6-Agnus.mid"),
    ("schubert", "death-and-the-maiden.mxl"),
]

CUTS = [0, 1, 97, 1000, 50, 99]  # byte cut points + percentage cuts


def _read(relparts):
    with open(os.path.join(CORPUS_ROOT, *relparts), "rb") as f:
        return f.read()


@pytest.mark.parametrize("relparts", CORPUS_FILES)
@pytest.mark.parametrize("cut", CUTS)
def test_truncated_files_fail_loudly(tmp_path, relparts, cut):
    data = _read(relparts)
    n = len(data) * cut // 100 if cut < 100 else min(cut, len(data))
    broken = tmp_path / ("broken" + os.path.splitext(relparts[-1])[1])
    broken.write_bytes(data[: max(n, 0)])
    with pytest.raises(IRParseError):
        load(broken)


def test_corrupted_zip_members_fail_loudly(tmp_path):
    """Rewrite an .mxl with its XML member bit-flipped; must not parse."""
    src = corpus_path("bach", "bwv227.1.mxl")
    data = _read(["bach", "bwv227.1.mxl"])
    rng = random.Random(227)
    flipped = bytearray(data)
    for _ in range(64):
        i = rng.randrange(len(flipped))
        flipped[i] ^= 0xFF
    broken = tmp_path / "flipped.mxl"
    broken.write_bytes(bytes(flipped))
    with pytest.raises(IRParseError):
        load(broken)
    # Also: a zip whose XML payload is corrupted while the container is fine.
    zin = zipfile.ZipFile(io.BytesIO(data))
    names = [n for n in zin.namelist() if "META-INF" not in n]
    payload = bytearray(zin.read(names[0]))
    for _ in range(256):
        i = rng.randrange(len(payload))
        payload[i] ^= 0xFF
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as zout:
        zout.writestr(names[0], bytes(payload))
    broken2 = tmp_path / "payload-corrupt.mxl"
    broken2.write_bytes(out.getvalue())
    with pytest.raises(IRParseError):
        load(broken2)


def test_corrupted_midi_fails_loudly(tmp_path):
    rng = random.Random(810)
    data = bytearray(_read(["byrd", "1-Kyrie.mid"]))
    for _ in range(32):
        i = rng.randrange(14, len(data))  # keep MThd header intact
        data[i] ^= 0xFF
    broken = tmp_path / "flipped.mid"
    broken.write_bytes(bytes(data))
    with pytest.raises(IRParseError):
        load(broken)
