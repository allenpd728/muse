"""Tests: S1 follow-up (issue #155).

- Full-corpus golden coverage: all 13 corpus files have committed vectors,
  verified against their sources, sizes pinned.
- Schema stability guard: dropping a required field fails verify loudly
  (not a KeyError or silent pass).
- Formatter drift guard: canonical_json's exact formatting pinned.
"""

import json
import os

import pytest

from muse_ir import load
from muse_stream import canonical_json, verify, work_to_canonical

from conftest import corpus_path

GOLDEN = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "golden"))

# (source parts, vector filename, pinned size in bytes) — measured 2026-08-23
VECTORS = {
    ("bach", "bwv227.1.mxl"): ("bach_bwv227.1.json", 40189),
    ("bach", "bwv227.3.mxl"): ("bach_bwv227.3.json", 54480),
    ("bach", "bwv227.7.mxl"): ("bach_bwv227.7.json", 46363),
    ("bach", "bwv227.11.mxl"): ("bach_bwv227.11.json", 29020),
    ("byrd", "1-Kyrie.mid"): ("byrd_1-kyrie.json", 11794),
    ("byrd", "2-Gloria.mid"): ("byrd_2-gloria.json", 139429),
    ("byrd", "3-Credo.mid"): ("byrd_3-credo.json", 215026),
    ("byrd", "4-Sanctu.mid"): ("byrd_4-sanctu.json", 48763),
    ("byrd", "5-Bened.mid"): ("byrd_5-bened.json", 20860),
    ("byrd", "6-Agnus.mid"): ("byrd_6-agnus.json", 57520),
    ("schubert", "death-and-the-maiden.mxl"): ("schubert_d810.json", 3809779),
    ("beethoven", "beethoven-sym5-mov1.xml"): ("beethoven_sym5_mov1.json", 2013010),
    ("beethoven", "beethoven-sym9.xml"): ("beethoven_sym9.json", 35858004),
}


class TestFullCorpusCoverage:
    @pytest.mark.parametrize("src", sorted(VECTORS))
    def test_vector_exists_and_verifies(self, src):
        name, _size = VECTORS[src]
        vector = os.path.join(GOLDEN, name)
        assert os.path.exists(vector), f"missing golden vector {name}"
        assert verify(corpus_path(*src), vector), f"verify failed for {name}"

    @pytest.mark.parametrize("src", sorted(VECTORS))
    def test_vector_size_pinned(self, src):
        name, size = VECTORS[src]
        actual = os.path.getsize(os.path.join(GOLDEN, name))
        assert actual == size, f"{name}: {actual} != pinned {size}"

    def test_every_corpus_file_has_a_vector(self):
        import glob
        corpus = os.path.normpath(os.path.join(GOLDEN, "..", "..", "..", "corpus"))
        on_disk = {
            os.path.relpath(f, corpus)
            for ext in ("*.xml", "*.mxl", "*.mid")
            for f in glob.glob(os.path.join(corpus, "*", ext))
        }
        covered = {os.path.join(*src) for src in VECTORS}
        assert on_disk == covered, f"uncovered: {on_disk - covered}"

    def test_no_machine_local_paths_in_vectors(self):
        # canonical form must be path-independent (regression: the Schubert
        # vector embedded '../../corpus/...' from a parser warning)
        import glob
        for f in glob.glob(os.path.join(GOLDEN, "*.json")):
            text = open(f).read()
            assert "../" not in text, f"{f} embeds a relative path"
            assert "/workspace" not in text, f"{f} embeds an absolute path"


class TestSchemaStability:
    def test_missing_required_field_fails_loudly(self, tmp_path):
        src = corpus_path("bach", "bwv227.1.mxl")
        doc = work_to_canonical(load(src))
        del doc["meta"]["ppq"]
        vector = tmp_path / "broken.json"
        vector.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n")
        assert not verify(src, str(vector))  # loud FAIL, not KeyError

    def test_missing_part_field_fails_loudly(self, tmp_path):
        src = corpus_path("bach", "bwv227.1.mxl")
        doc = work_to_canonical(load(src))
        del doc["parts"][0]["notes"][0]["onset"]
        vector = tmp_path / "broken.json"
        vector.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n")
        assert not verify(src, str(vector))

    def test_missing_top_level_field_fails_loudly(self, tmp_path):
        src = corpus_path("bach", "bwv227.1.mxl")
        doc = work_to_canonical(load(src))
        del doc["maps"]
        vector = tmp_path / "broken.json"
        vector.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n")
        assert not verify(src, str(vector))


class TestFormatterDrift:
    def test_canonical_prefix_pinned(self):
        work = load(corpus_path("bach", "bwv227.1.mxl"))
        text = canonical_json(work)
        # exact formatting contract: sorted keys, no spaces, meta first
        assert text.startswith('{"maps":{"key":[[0,1,"minor"]],"meter":[[0,4,4]],"tempo":[[0,96000]]},"meta":{')
        assert text.endswith("}\n")
        assert text.count("\n") == 1  # single trailing newline, no wrapping

    def test_key_order_is_sorted(self):
        work = load(corpus_path("bach", "bwv227.1.mxl"))
        doc = json.loads(canonical_json(work))
        assert list(doc) == sorted(doc)
        assert list(doc["meta"]) == sorted(doc["meta"])
