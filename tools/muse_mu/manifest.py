"""S5 container + manifest — .mu zip layout and the plaintext rights manifest.

The manifest is the only human-readable member, by design: a lawyer reads
it with a text editor. It carries license, provenance (with AI disclosure),
and content hashes of every other member. Decisions: SHA-256 for hashes;
signature as an optional HMAC-SHA256 field (PKI deferred — open question
recorded in the spec decisions log).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import zipfile
from dataclasses import dataclass, field


class ManifestError(ValueError):
    """Raised when a manifest or container violates the S5 schema."""


REQUIRED_MEMBERS = ("manifest.json", "roll.bin", "seed.bin")
OPTIONAL_DIRS = ("performances/",)

LICENSE_RENDITIONS = frozenset({
    "presets-only",
    "open-within-constraints",
    "closed",
})

MANIFEST_KEYS = frozenset({
    "format_version", "work_id", "title", "composer", "license",
    "provenance", "hashes", "signature",
})
REQUIRED_MANIFEST_KEYS = frozenset({
    "format_version", "work_id", "license", "provenance", "hashes",
})
LICENSE_KEYS = frozenset({"renditions", "attribution", "commercial"})
PROVENANCE_KEYS = frozenset({
    "source", "tools", "ai_involvement", "author", "license_ref",
})


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class Manifest:
    format_version: str
    work_id: str
    license: dict
    provenance: dict
    hashes: dict                              # member name -> sha256 hex
    title: str = ""
    composer: str = ""
    signature: str = ""                       # optional HMAC-SHA256 hex

    def validate(self):
        d = self.to_dict(include_optional=False)
        required_missing = {k for k in REQUIRED_MANIFEST_KEYS if not d.get(k)}
        if required_missing:
            raise ManifestError(f"missing required keys: {sorted(required_missing)}")
        if not isinstance(dict(self.__dict__).get("signature", ""), str):
            raise ManifestError("signature must be a string")
        self._validate_license()
        self._validate_provenance()
        self._validate_hashes()

    def _validate_license(self):
        if not isinstance(self.license, dict):
            raise ManifestError("license must be a mapping")
        unknown = set(self.license) - LICENSE_KEYS
        if unknown:
            raise ManifestError(f"unknown license keys: {sorted(unknown)}")
        renditions = self.license.get("renditions")
        if renditions not in LICENSE_RENDITIONS:
            raise ManifestError(
                f"license.renditions must be one of {sorted(LICENSE_RENDITIONS)}, "
                f"got {renditions!r}")
        if not self.license.get("attribution"):
            raise ManifestError("license.attribution is required")
        if not isinstance(self.license.get("commercial"), bool):
            raise ManifestError("license.commercial must be a boolean")

    def _validate_provenance(self):
        if not isinstance(self.provenance, dict):
            raise ManifestError("provenance must be a mapping")
        unknown = set(self.provenance) - PROVENANCE_KEYS
        if unknown:
            raise ManifestError(f"unknown provenance keys: {sorted(unknown)}")
        if not self.provenance.get("source"):
            raise ManifestError("provenance.source is required")
        if not self.provenance.get("author"):
            raise ManifestError("provenance.author is required")
        ai = self.provenance.get("ai_involvement")
        if ai not in ("none", "assisted", "generated"):
            raise ManifestError(
                "provenance.ai_involvement must be 'none' | 'assisted' | 'generated' "
                "(AI disclosure is mandatory)")
        tools = self.provenance.get("tools")
        if tools is not None and not isinstance(tools, list):
            raise ManifestError("provenance.tools must be a list")

    def _validate_hashes(self):
        if not isinstance(self.hashes, dict) or not self.hashes:
            raise ManifestError("hashes must be a non-empty mapping")
        for member, digest in self.hashes.items():
            if member == "manifest.json":
                raise ManifestError("manifest must not hash itself")
            if not isinstance(digest, str) or len(digest) != 64:
                raise ManifestError(f"hashes[{member!r}]: not a sha256 hex digest")
            try:
                int(digest, 16)
            except ValueError:
                raise ManifestError(f"hashes[{member!r}]: not a sha256 hex digest")

    def to_dict(self, include_optional=True):
        d = {
            "format_version": self.format_version,
            "work_id": self.work_id,
            "license": self.license,
            "provenance": self.provenance,
            "hashes": self.hashes,
        }
        if include_optional:
            if self.title:
                d["title"] = self.title
            if self.composer:
                d["composer"] = self.composer
            if self.signature:
                d["signature"] = self.signature
        return d

    def sign(self, key: bytes):
        """HMAC-SHA256 over the canonical manifest minus the signature field."""
        payload = dict(self.to_dict())
        payload.pop("signature", None)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        self.signature = hmac.new(key, canonical, hashlib.sha256).hexdigest()

    def verify(self, key: bytes) -> bool:
        if not self.signature:
            raise ManifestError("no signature to verify")
        expected = Manifest(**{**self.__dict__, "signature": ""})
        expected.sign(key)
        return hmac.compare_digest(expected.signature, self.signature)

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise ManifestError("manifest must be a mapping")
        unknown = set(d) - MANIFEST_KEYS
        if unknown:
            raise ManifestError(f"unknown manifest keys: {sorted(unknown)}")
        m = cls(
            format_version=d.get("format_version", ""),
            work_id=d.get("work_id", ""),
            title=d.get("title", ""),
            composer=d.get("composer", ""),
            license=d.get("license", {}),
            provenance=d.get("provenance", {}),
            hashes=d.get("hashes", {}),
            signature=d.get("signature", ""),
        )
        m.validate()
        return m

    @classmethod
    def from_json(cls, text: str):
        try:
            d = json.loads(text)
        except json.JSONDecodeError as e:
            raise ManifestError(f"manifest is not valid JSON: {e}") from e
        return cls.from_dict(d)

    def to_json(self) -> str:
        self.validate()
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def build_manifest(work_id, license, provenance, members: dict,
                   format_version="0.1", title="", composer="") -> Manifest:
    """Construct a manifest hashing the given {member_name: bytes}."""
    m = Manifest(
        format_version=format_version,
        work_id=work_id,
        title=title,
        composer=composer,
        license=license,
        provenance=provenance,
        hashes={name: sha256_hex(data) for name, data in sorted(members.items())},
    )
    m.validate()
    return m


def write_mu(path, manifest: Manifest, members: dict):
    """Write a .mu zip: manifest.json first, then members in sorted order."""
    manifest.validate()
    expected = {name: sha256_hex(data) for name, data in members.items()}
    if expected != manifest.hashes:
        raise ManifestError("manifest hashes do not match provided members")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", manifest.to_json())
        for name in sorted(members):
            z.writestr(name, members[name])


def read_mu(path, verify_hashes=True) -> tuple:
    """Read a .mu container: (Manifest, {member: bytes}). Fails loudly on
    layout violations and (by default) hash mismatches."""
    try:
        z = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as e:
        raise ManifestError(f"not a .mu zip container: {e}") from e
    with z:
        names = z.namelist()
        for req in REQUIRED_MEMBERS:
            if req not in names:
                raise ManifestError(f"required member {req!r} missing")
        for name in names:
            if name in REQUIRED_MEMBERS:
                continue
            if not name.startswith(OPTIONAL_DIRS):
                raise ManifestError(f"unexpected member {name!r}")
        manifest = Manifest.from_json(z.read("manifest.json").decode("utf-8"))
        members = {n: z.read(n) for n in names if n != "manifest.json"}
    if verify_hashes:
        for name, digest in manifest.hashes.items():
            if name not in members:
                raise ManifestError(f"hashed member {name!r} not in container")
            actual = sha256_hex(members[name])
            if actual != digest:
                raise ManifestError(
                    f"hash mismatch on {name!r}: manifest {digest[:12]}… "
                    f"vs content {actual[:12]}…")
        unhashed = set(members) - set(manifest.hashes)
        if unhashed:
            raise ManifestError(f"members missing from hashes: {sorted(unhashed)}")
    return manifest, members
