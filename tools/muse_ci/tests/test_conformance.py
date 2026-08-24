"""P3 conformance gate: fast tier.

The full verify runs in ~2s (decode-only — no source re-parse), so the
fast tier exercises the whole 13-work registry. Vector-store integrity,
tamper detection, determinism, and CLI behavior live here; regeneration
fidelity (corpus → .mu) is covered by test_conformance_full.py.
"""

import json
import os
import shutil
import zipfile

import pytest

from muse_ci import (
    FAST_REGISTRY,
    PINS_FORMAT,
    PINS_NAME,
    REGISTRY,
    VECTORS_DIR,
    decoded_canonical,
    verify,
)
from muse_ci.cli import main as cli_main


class TestVectorGate:
    @pytest.mark.parametrize("work_id,relpath", REGISTRY)
    def test_vector_conforms(self, work_id, relpath):
        (r,) = verify(registry=[(work_id, relpath)])
        assert r.status == "PASS", f"{work_id}: {r.detail}"

    def test_verify_all_pass(self):
        results = verify(registry=REGISTRY)
        assert all(r.status == "PASS" for r in results)
        assert len(results) == len(REGISTRY)


class TestStoreIntegrity:
    def _pins(self):
        with open(os.path.join(VECTORS_DIR, PINS_NAME)) as fh:
            return json.load(fh)

    def test_pins_format_version(self):
        assert self._pins()["format"] == PINS_FORMAT

    def test_every_registry_work_pinned(self):
        vectors = self._pins()["vectors"]
        assert {wid for wid, _ in REGISTRY} == set(vectors)

    def test_pin_schema(self):
        for work_id, entry in self._pins()["vectors"].items():
            assert set(entry) == {"source", "mu", "sha256", "canonical_bytes"}
            assert len(entry["sha256"]) == 64
            int(entry["sha256"], 16)
            assert entry["canonical_bytes"] > 0
            assert entry["mu"] == f"{work_id}.mu"
            assert not entry["source"].startswith("/")
            assert "../" not in entry["source"]

    def test_every_pin_has_mu_on_disk(self):
        for entry in self._pins()["vectors"].values():
            assert os.path.exists(os.path.join(VECTORS_DIR, entry["mu"]))

    def test_containers_are_valid_mu(self):
        from muse_mu import read_mu

        for work_id, _ in FAST_REGISTRY:
            manifest, members = read_mu(os.path.join(VECTORS_DIR, f"{work_id}.mu"))
            assert set(members) == {"roll.bin", "seed.bin"}
            assert manifest.work_id == work_id


class TestTamperDetection:
    def _copy_store(self, tmp_path, work_id="bach-bwv227.1"):
        store = tmp_path / "vectors"
        store.mkdir()
        shutil.copy(os.path.join(VECTORS_DIR, PINS_NAME), store / PINS_NAME)
        shutil.copy(os.path.join(VECTORS_DIR, f"{work_id}.mu"), store / f"{work_id}.mu")
        return store

    def test_corrupted_pin_fails(self, tmp_path):
        store = self._copy_store(tmp_path)
        pins = json.loads((store / PINS_NAME).read_text())
        pins["vectors"]["bach-bwv227.1"]["sha256"] = "0" * 64
        (store / PINS_NAME).write_text(json.dumps(pins))
        (r,) = verify(str(store), registry=[("bach-bwv227.1", "bach/bwv227.1.mxl")])
        assert r.status == "FAIL"
        assert "sha256" in r.detail

    def test_flipped_roll_byte_fails(self, tmp_path):
        store = self._copy_store(tmp_path)
        mu = store / "bach-bwv227.1.mu"
        with zipfile.ZipFile(mu) as zf:
            members = {n: zf.read(n) for n in zf.namelist()}
        roll = bytearray(members["roll.bin"])
        roll[len(roll) // 2] ^= 0xFF
        members["roll.bin"] = bytes(roll)
        with zipfile.ZipFile(mu, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, data in members.items():
                zf.writestr(name, data)
        (r,) = verify(str(store), registry=[("bach-bwv227.1", "bach/bwv227.1.mxl")])
        assert r.status == "FAIL"

    def test_missing_mu_fails(self, tmp_path):
        store = self._copy_store(tmp_path)
        os.remove(store / "bach-bwv227.1.mu")
        (r,) = verify(str(store), registry=[("bach-bwv227.1", "bach/bwv227.1.mxl")])
        assert r.status == "FAIL"
        assert "missing" in r.detail

    def test_missing_pin_entry_fails(self, tmp_path):
        store = self._copy_store(tmp_path)
        pins = json.loads((store / PINS_NAME).read_text())
        del pins["vectors"]["bach-bwv227.1"]
        (store / PINS_NAME).write_text(json.dumps(pins))
        (r,) = verify(str(store), registry=[("bach-bwv227.1", "bach/bwv227.1.mxl")])
        assert r.status == "FAIL"
        assert "no pin" in r.detail


class TestDeterminism:
    def test_decode_is_deterministic(self):
        mu = os.path.join(VECTORS_DIR, "byrd-2-gloria.mu")
        assert decoded_canonical(mu) == decoded_canonical(mu)


class TestCli:
    def test_cli_verify_passes(self, capsys):
        assert cli_main(["verify"]) == 0
        assert "verify: PASS" in capsys.readouterr().out

    def test_cli_verify_full_passes(self, capsys):
        assert cli_main(["verify", "--full"]) == 0

    def test_cli_verify_fails_on_tampered_store(self, tmp_path, capsys):
        store = tmp_path / "vectors"
        store.mkdir()
        shutil.copy(os.path.join(VECTORS_DIR, PINS_NAME), store / PINS_NAME)
        shutil.copy(os.path.join(VECTORS_DIR, "byrd-1-kyrie.mu"),
                    store / "byrd-1-kyrie.mu")
        pins = json.loads((store / PINS_NAME).read_text())
        pins["vectors"]["byrd-1-kyrie"]["canonical_bytes"] = 1
        pins["vectors"]["byrd-1-kyrie"]["sha256"] = "f" * 64
        (store / PINS_NAME).write_text(json.dumps(pins))
        rc = cli_main(["verify", "--vectors", str(store)])
        assert rc == 1
        assert "verify: FAIL" in capsys.readouterr().out

    def test_cli_dump(self, tmp_path):
        out = tmp_path / "actual.json"
        assert cli_main(["dump", "bach-bwv227.1", "-o", str(out)]) == 0
        doc = json.loads(out.read_text())
        assert set(doc) == {"s1_version", "meta", "maps", "parts"}
