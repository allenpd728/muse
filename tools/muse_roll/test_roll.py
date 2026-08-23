"""S2 roll encoding tests (issue #138).

Lossless round-trips (W4 ground truth), codec primitives, malformed
inputs, determinism, and the corpus gate.
"""

import os
import subprocess
import sys

import pytest

from muse_ir import load
from muse_ir.model import (
    DynamicMarking,
    Hairpin,
    Instrument,
    Maps,
    Meta,
    Note,
    Part,
    Work,
)
from muse_roll import RollError, decode, encode, verify_round_trip
from muse_roll.roll import _Reader, _sv, _uv

DIR = os.path.dirname(__file__)
CLI = os.path.join(DIR, "cli.py")
CORPUS = os.path.normpath(os.path.join(DIR, "..", "..", "corpus"))

BACH1 = os.path.join(CORPUS, "bach", "bwv227.1.mxl")
KYRIE = os.path.join(CORPUS, "byrd", "1-Kyrie.mid")
SCHUBERT = os.path.join(CORPUS, "schubert", "death-and-the-maiden.mxl")
B5 = os.path.join(CORPUS, "beethoven", "beethoven-sym5-mov1.xml")


def rich_work():
    """Synthetic work exercising every codec path."""
    return Work(
        parts=[Part(
            id="P1", name="Cello",
            instrument=Instrument(name="Violoncello", gm_program=42),
            inferred_voice=True,
            notes=[
                Note(pitch=48, onset=0, duration=480, voice=1, velocity=64,
                     articulations=("staccato",), notations=frozenset({"slur_start"}),
                     source_id="n1"),
                Note(pitch=None, onset=480, duration=480),  # rest
                Note(pitch=None, onset=960, duration=240, notations=frozenset({"unpitched"})),
                Note(pitch=50, onset=1200, duration=0, voice=2,
                     velocity_inferred=True, notations=frozenset({"grace", "tie_start"})),
            ],
            dynamics=[DynamicMarking(tick=0, text="pp"), DynamicMarking(tick=480, text="sfz")],
            hairpins=[Hairpin(kind="crescendo", start_tick=0, end_tick=480),
                      Hairpin(kind="diminuendo", start_tick=480, end_tick=None)],
        )],
        maps=Maps(tempo=[(0, 96000), (480, 60000)],
                  meter=[(0, 4, 4), (480, 3, 8)],
                  key=[(0, -3, "minor"), (480, 2, "major")]),
        meta=Meta(source_format="musicxml", ppq=480, title="Ünïcode Títle",
                  warnings=["w1", "w2"]),
    )


class TestVarintPrimitives:
    @pytest.mark.parametrize("n", [0, 1, 127, 128, 300, 16384, 2**35])
    def test_unsigned_round_trip(self, n):
        r = _Reader(_uv(n))
        assert r.uv() == n

    @pytest.mark.parametrize("n", [0, 1, -1, 63, -64, 1000, -1000, 2**40, -(2**40)])
    def test_signed_round_trip(self, n):
        r = _Reader(_sv(n))
        assert r.sv() == n

    def test_negative_unsigned_rejected(self):
        with pytest.raises(RollError):
            _uv(-1)

    def test_truncated_varint_loud(self):
        with pytest.raises(RollError, match="truncated"):
            _Reader(b"\x80").uv()


class TestRoundTrip:
    def test_rich_work_lossless(self):
        assert verify_round_trip(rich_work())

    def test_encode_deterministic(self):
        w = rich_work()
        assert encode(w) == encode(w)

    def test_corpus_small_works(self):
        for f in (BACH1, KYRIE):
            assert verify_round_trip(load(f)), f

    def test_schubert_with_dynamics_and_hairpins(self):
        assert verify_round_trip(load(SCHUBERT))

    def test_beethoven5(self):
        assert verify_round_trip(load(B5))


class TestMalformedInputs:
    def test_bad_magic(self):
        with pytest.raises(RollError, match="bad magic"):
            decode(b"XXXX" + b"\x00" * 10)

    def test_truncated_payload(self):
        data = encode(rich_work())
        with pytest.raises(RollError):
            decode(data[: len(data) // 2])

    def test_corrupt_zlib(self):
        data = bytearray(encode(rich_work()))
        data[-5] ^= 0xFF
        with pytest.raises(RollError):
            decode(bytes(data))

    def test_not_bytes(self):
        with pytest.raises(RollError):
            decode("not bytes")

    def test_string_table_out_of_range(self):
        # craft a payload with a dangling string index
        good = encode(rich_work())
        with pytest.raises(RollError):
            decode(good[:20] + b"\xff" + good[21:])


class TestCLI:
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, CLI, *args],
            capture_output=True, text=True, timeout=600,
            cwd=os.path.join(DIR, ".."),
        )

    def test_pack_verify_lossless(self, tmp_path):
        roll = str(tmp_path / "w.roll.bin")
        r = self.run_cli("pack", BACH1, "-o", roll)
        assert r.returncode == 0, r.stderr
        r = self.run_cli("verify", BACH1, roll)
        assert r.returncode == 0
        assert "LOSSLESS" in r.stdout

    def test_verify_tampered_roll_fails(self, tmp_path):
        roll = tmp_path / "w.roll.bin"
        roll.write_bytes(encode(load(BACH1)))
        blob = bytearray(roll.read_bytes())
        blob[-10] ^= 0xFF
        roll.write_bytes(bytes(blob))
        r = self.run_cli("verify", BACH1, str(roll))
        assert r.returncode == 1

    def test_unpack_summary(self, tmp_path):
        roll = str(tmp_path / "w.roll.bin")
        self.run_cli("pack", KYRIE, "-o", roll)
        r = self.run_cli("unpack", roll)
        assert r.returncode == 0
        assert '"notes": 71' in r.stdout
