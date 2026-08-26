"""S3.8a lineage walker tests (Tests: #260, spec tests/closed_*)."""

import json
import os
import subprocess
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_lineage.lineage import (  # noqa: E402
    LineageError, find_by_hash, sha256_file, verify_pair, walk,
)

CLI = os.path.join(os.path.dirname(__file__), "cli.py")
REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _seed(path, extends=None, seed_hash=None):
    prov = {"author": "t", "ai_assisted": True}
    if extends is not None:
        prov["extends"] = extends
    if seed_hash is not None:
        prov["seed_hash"] = seed_hash
    path.write_text(yaml.safe_dump({"provenance": prov}))
    return str(path)


def _chain(tmp_path, n=3):
    """v1 (root) ← v2 ← ... ← vn. Returns paths in order."""
    paths = []
    for i in range(1, n + 1):
        extends = sha256_file(paths[-1]) if paths else None
        paths.append(_seed(tmp_path / f"v{i}.seed.yaml", extends=extends))
    return paths


def test_walk_three_revision_chain_all_verified(tmp_path):
    paths = _chain(tmp_path)
    hops = walk(paths[-1], [str(tmp_path)])
    assert [h.status for h in hops] == ["verified", "verified", "root"]
    assert hops[0].parent == paths[1]
    assert hops[1].parent == paths[0]


def test_walk_missing_parent_stops(tmp_path):
    paths = _chain(tmp_path, 2)
    # repoint v2's extends at a hash nothing has
    _seed(tmp_path / "v2.seed.yaml",
          extends="f" * 64)
    hops = walk(paths[-1], [str(tmp_path)])
    assert [h.status for h in hops] == ["missing"]


def test_verify_pair_mismatch_and_verified(tmp_path):
    paths = _chain(tmp_path, 2)
    assert verify_pair(paths[1], paths[0]) == "verified"
    # genuinely different bytes (a bare root seed is byte-identical to v1)
    tampered = tmp_path / "tampered.seed.yaml"
    tampered.write_text(open(paths[0]).read() + "# tampered\n")
    assert verify_pair(paths[1], str(tampered)) == "mismatch"


def test_root_seed_single_hop(tmp_path):
    p = _seed(tmp_path / "root.seed.yaml")
    hops = walk(p, [str(tmp_path)])
    assert len(hops) == 1 and hops[0].status == "root"


def test_yaml_coerced_zero_hash_is_missing_not_root(tmp_path):
    """Regression: an unquoted 64-zero extends parses as int 0 — it must
    report missing, never masquerade as root."""
    p = tmp_path / "orphan.seed.yaml"
    p.write_text("provenance:\n  author: t\n  ai_assisted: true\n"
                 f"  extends: {'0' * 64}\n")
    hops = walk(str(p), [str(tmp_path)])
    assert [h.status for h in hops] == ["missing"]


def test_mockup_hop_continues_to_seed(tmp_path):
    """seed v2 → mockup (seed_hash) → seed v1: the S3.8b seam."""
    v1 = _seed(tmp_path / "w.v1.seed.yaml")
    mockup = tmp_path / "w.v1.mockup.json"
    mockup.write_text(json.dumps(
        {"work_id": "w", "tempo_map": [], "parts": {},
         "provenance": {"seed_hash": sha256_file(v1)}}))
    v2 = _seed(tmp_path / "w.v2.seed.yaml", extends=sha256_file(str(mockup)))
    hops = walk(v2, [str(tmp_path)])
    assert [h.status for h in hops] == ["verified", "verified", "root"]


def test_real_chain_bwv227(tmp_path):
    """Known-answer pin: the committed v3→mockup→v2→root chain verifies.
    Drift here means a link broke; re-stamping must be deliberate."""
    seeds = os.path.join(REPO, "seeds")
    v3 = os.path.join(seeds, "bwv227.1.v3.seed.yaml")
    if not os.path.exists(v3):
        pytest.skip("v3 chain not committed in this checkout")
    hops = walk(v3, [seeds])
    assert [h.status for h in hops] == ["verified"] * 3 + ["root"]


def test_cycle_guard_terminates(tmp_path):
    """Content-addressed cycles can't be written to disk (the child's
    bytes must contain the parent's hash), so rig the store: two files,
    find_by_hash forced to alternate between them. The walk must
    terminate with a cycle hop."""
    a = _seed(tmp_path / "a.seed.yaml", extends="a" * 64)
    b = _seed(tmp_path / "b.seed.yaml", extends="b" * 64)
    import muse_lineage.lineage as lin
    alt = {a: b, b: a}
    orig = lin.find_by_hash
    # key the alternation off the pointer each hop is chasing
    seen = []
    def fake_find(digest, dirs):
        seen.append(digest)
        return alt[a] if len(seen) % 2 else alt[b]
    lin.find_by_hash = fake_find
    try:
        hops = walk(a, [str(tmp_path)])
    finally:
        lin.find_by_hash = orig
    assert hops[-1].status == "cycle"


def test_cli_exit_codes(tmp_path):
    paths = _chain(tmp_path, 2)
    ok = subprocess.run([sys.executable, CLI, "walk", paths[1],
                         "--store", str(tmp_path)],
                        capture_output=True, text=True, cwd=REPO)
    assert ok.returncode == 0 and "verified" in ok.stdout
    bad = subprocess.run([sys.executable, CLI, "verify", paths[1], paths[0]],
                         capture_output=True, text=True, cwd=REPO)
    assert bad.returncode == 0 and bad.stdout.strip() == "verified"
    tampered = tmp_path / "t.seed.yaml"
    tampered.write_text(open(paths[0]).read() + "# tampered\n")
    mm = subprocess.run([sys.executable, CLI, "verify", paths[1],
                         str(tampered)],
                        capture_output=True, text=True, cwd=REPO)
    assert mm.returncode == 1 and mm.stdout.strip() == "mismatch"


def test_cli_json_shape(tmp_path):
    paths = _chain(tmp_path, 2)
    proc = subprocess.run([sys.executable, CLI, "walk", paths[1],
                           "--store", str(tmp_path), "--json"],
                          capture_output=True, text=True)
    d = json.loads(proc.stdout)
    assert d["ok"] is True
    assert set(d["hops"][0]) == {"child", "pointer", "status", "parent"}


def test_find_by_hash_empty_store(tmp_path):
    assert find_by_hash("a" * 64, [str(tmp_path)]) == ""


def test_unparseable_child_raises(tmp_path):
    bad = tmp_path / "bad.seed.yaml"
    bad.write_text("{not: [yaml")
    with pytest.raises(LineageError):
        walk(str(bad), [str(tmp_path)])
