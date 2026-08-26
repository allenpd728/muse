"""Lineage chain-walk/verify (S3.8a, #251).

Walks `provenance.extends` (seeds, S3.7) / `provenance.seed_hash`
(mockups, L1.10) backward through the artifact store. Hash convention:
bare 64-hex SHA-256 of the parent artifact's committed file bytes
(same digest shape as `muse_mu.manifest.sha256_hex`).

Per-hop states:
- verified  — a store file's bytes hash to the pointer (or the explicit
              pair matches in verify_pair)
- missing   — no store file hashes to the pointer (deleted, never
              committed, or corrupted in place — indistinguishable by
              hash alone)
- mismatch  — explicit pair check only: the named parent's bytes do NOT
              hash to the child's pointer
- root      — no pointer; the chain's origin
- cycle     — a file already visited re-entered (broken store)
"""

from __future__ import annotations

import glob
import hashlib
import os
from dataclasses import dataclass, field

import yaml


class LineageError(Exception):
    pass


def sha256_file(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _back_pointer(path: str):
    """The hash naming this artifact's parent: extends (seeds/manifests)
    or seed_hash (mockups). None for a root or an artifact without
    provenance."""
    try:
        data = yaml.safe_load(open(path).read())
    except yaml.YAMLError as e:
        raise LineageError(f"{path}: unparseable: {e}")
    if not isinstance(data, dict):
        return None
    prov = data.get("provenance")
    if not isinstance(prov, dict):
        return None
    # Key presence, not truthiness: YAML reads a 64-zero hash as int 0,
    # and a falsy pointer must not masquerade as a root.
    if "extends" in prov:
        return prov["extends"]
    return prov.get("seed_hash")


@dataclass
class Hop:
    child: str
    pointer: str = ""
    status: str = "root"          # root | verified | missing | cycle
    parent: str = ""

    def to_dict(self):
        return {"child": self.child, "pointer": self.pointer,
                "status": self.status, "parent": self.parent}


def store_files(dirs):
    """Candidate parent artifacts: committed seed revisions and mockups."""
    out = []
    for d in dirs:
        for pat in ("*.seed.yaml", "*.mockup.json"):
            out.extend(glob.glob(os.path.join(d, "**", pat), recursive=True))
    return sorted(set(out))


def find_by_hash(digest: str, dirs) -> str:
    """First store file whose bytes hash to digest, or ''."""
    for path in store_files(dirs):
        if sha256_file(path) == digest:
            return path
    return ""


def verify_pair(child_path: str, parent_path: str) -> str:
    """Explicit two-artifact check: does the child's pointer name exactly
    these parent bytes? Returns verified | mismatch."""
    pointer = _back_pointer(child_path)
    if not pointer:
        raise LineageError(f"{child_path}: no lineage pointer (root artifact)")
    return "verified" if sha256_file(parent_path) == pointer else "mismatch"


def walk(seed_path: str, store_dirs, max_hops: int = 64):
    """Walk backward from seed_path. Stops at root, missing, or cycle."""
    hops = []
    current = seed_path
    seen = set()
    for _ in range(max_hops):
        if current in seen:
            hops.append(Hop(child=current, status="cycle"))
            break
        seen.add(current)
        pointer = _back_pointer(current)
        if pointer is None:
            hops.append(Hop(child=current, status="root"))
            break
        if not isinstance(pointer, str):
            # Malformed pointer (e.g. YAML-coerced scalar) — unresolvable.
            hops.append(Hop(child=current, pointer=str(pointer),
                            status="missing"))
            break
        parent = find_by_hash(pointer, store_dirs)
        if not parent:
            hops.append(Hop(child=current, pointer=pointer, status="missing"))
            break
        hops.append(Hop(child=current, pointer=pointer,
                        status="verified", parent=parent))
        current = parent
    return hops


@dataclass
class ChainReport:
    hops: list = field(default_factory=list)

    @property
    def ok(self):
        return bool(self.hops) and all(
            h.status in ("verified", "root") for h in self.hops)
