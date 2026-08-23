"""S2 packer tests — W4 diff gate over corpus tiers."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "corpus_loader"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "muse_diff"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

import muse_corpus  # noqa: E402
from muse_diff.diff import diff  # noqa: E402

from muse_pack.pack import pack, unpack  # noqa: E402
from muse_pack.rebuild import unpack_to_canonical  # noqa: E402

CORPUS_FILES = [
    "bach/bwv227.1.mxl",
    "byrd/2-Gloria.mid",
    "schubert/death-and-the-maiden.mxl",
    "beethoven/beethoven-sym5-mov1.xml",
]

# Packed-vs-source ratio bands measured at task time (packed includes all
# channels + meta/maps; source is the corpus file on disk).
EXPECTED_RATIO = {
    "bach/bwv227.1.mxl": (0.14, 0.30),
    "byrd/2-Gloria.mid": (0.16, 0.42),
    "schubert/death-and-the-maiden.mxl": (0.08, 0.20),
    "beethoven/beethoven-sym5-mov1.xml": (0.001, 0.012),
}


def _work_from_unpacked(payload):
    from muse_ir.model import Maps, Meta, Note, Part, Work

    parts = []
    for p in payload["parts"]:
        notes = [
            Note(
                pitch=n["pitch"],
                onset=n["onset"],
                duration=n["duration"],
                voice=n["voice"],
                velocity=n["velocity"],
                notations=frozenset(n["notations"]),
            )
            for n in p["notes"]
        ]
        parts.append(Part(id=p["id"], name=p["name"], notes=notes))
    return Work(
        parts=parts,
        maps=Maps(),
        meta=Meta(
            source_format=payload["meta"]["source_format"],
            ppq=payload["meta"]["ppq"],
        ),
    )


@pytest.mark.parametrize("relpath", CORPUS_FILES)
def test_roundtrip_w4_diff(relpath):
    """Lossless by W4's diff: recall == precision == 1.0."""
    work = muse_corpus.load_file(relpath)
    unpacked = unpack_to_canonical(unpack(pack(work)))
    restored = _work_from_unpacked(unpacked)
    report = diff(work, restored)
    assert report.ok(), (
        f"{relpath}: recall={report.recall:.4f} precision={report.precision:.4f}"
    )


@pytest.mark.parametrize("relpath", list(EXPECTED_RATIO))
def test_compression_ratio(relpath):
    """Packed size must sit in the ratio band measured at task time."""
    lo, hi = EXPECTED_RATIO[relpath]
    src = os.path.getsize(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "corpus", relpath)
    )
    packed = pack(muse_corpus.load_file(relpath))
    ratio = len(packed) / src
    assert lo <= ratio <= hi, f"{relpath}: ratio {ratio:.3f} outside [{lo}, {hi}]"


def test_packed_deterministic():
    """Same Work → identical payload (byte-stable)."""
    work = muse_corpus.load_file("bach/bwv227.1.mxl")
    assert pack(work) == pack(work)
