"""Seed model + validation for S3.1 container & encoding."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


class SeedError(ValueError):
    """Raised when a seed violates the S3.1 schema."""


TOP_LEVEL_KEYS = {
    "format_version", "work_id", "title", "params", "philosophy",
    "variation_points", "assertions", "provenance", "era_budget",
}

REQUIRED_KEYS = {"format_version", "work_id", "params", "assertions"}

# Lineage fields (S3.7, #248): extends is the bare 64-hex SHA-256 of the
# parent artifact's committed bytes; operation is the tool@version that
# produced the revision. Both optional; omitted on a root seed.
_OPERATION_RE = re.compile(r"^[a-z][a-z0-9_]*@\d+(\.\d+)*$")


def is_sha256_hex(value) -> bool:
    """Bare 64-char lowercase-or-upper hex digest — the manifest's shape."""
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


@dataclass
class Seed:
    format_version: str
    work_id: str
    title: str = ""
    params: dict = field(default_factory=dict)
    philosophy: dict = field(default_factory=dict)
    variation_points: list = field(default_factory=list)
    assertions: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    era_budget: dict | None = None  # optional (S3 decisions log, 2026-08-24)

    def to_dict(self):
        d = {
            "format_version": self.format_version,
            "work_id": self.work_id,
            "title": self.title,
            "params": self.params,
            "philosophy": self.philosophy,
            "variation_points": self.variation_points,
            "assertions": self.assertions,
            "provenance": self.provenance,
        }
        if self.era_budget is not None:
            d["era_budget"] = self.era_budget
        return d


def validate_seed(seed: Seed):
    """S3.1 schema checks. Fail loudly on unknown/missing keys."""
    missing = REQUIRED_KEYS - {k for k, v in seed.to_dict().items() if v}
    if missing:
        raise SeedError(f"missing required keys: {sorted(missing)}")
    unknown = set(seed.to_dict()) - TOP_LEVEL_KEYS
    if unknown:
        raise SeedError(f"unknown top-level keys: {sorted(unknown)}")
    if not isinstance(seed.params, dict):
        raise SeedError("params must be a mapping")
    if not isinstance(seed.assertions, dict):
        raise SeedError("assertions must be a mapping")
    if not isinstance(seed.variation_points, list):
        raise SeedError("variation_points must be a list")
    if seed.era_budget is not None and not isinstance(seed.era_budget, dict):
        raise SeedError("era_budget must be a mapping when present")
    _validate_provenance(seed.provenance)
    if seed.variation_points:
        from muse_seed.variation import VariationError, validate_variation_points

        try:
            validate_variation_points(seed.variation_points)
        except VariationError as e:
            raise SeedError(f"variation_points: {e}") from e
    if seed.philosophy:
        from muse_seed.philosophy import Philosophy, PhilosophyError

        try:
            Philosophy.from_dict(seed.philosophy)
        except PhilosophyError as e:
            raise SeedError(f"philosophy: {e}") from e


def _validate_provenance(provenance):
    """Shape-check the optional lineage fields (S3.7). Provenance keys are
    otherwise free-form — only extends/operation carry a contract."""
    if not isinstance(provenance, dict):
        raise SeedError("provenance must be a mapping")
    if "extends" in provenance and not is_sha256_hex(provenance["extends"]):
        raise SeedError(
            "provenance.extends must be a bare 64-hex sha256 of the parent "
            "artifact's committed bytes"
        )
    if "operation" in provenance:
        op = provenance["operation"]
        if not isinstance(op, str) or not _OPERATION_RE.match(op):
            raise SeedError(
                "provenance.operation must be tool@version (e.g. muse_distill@1)"
            )


def load_seed(data: str, fmt: str = "yaml") -> Seed:
    """Parse YAML-or-JSON into a Seed; validate."""
    if fmt == "json":
        d = json.loads(data)
    else:
        import yaml
        d = yaml.safe_load(data)
    seed = Seed(
        format_version=d.get("format_version", ""),
        work_id=d.get("work_id", ""),
        title=d.get("title", ""),
        params=d.get("params", {}),
        philosophy=d.get("philosophy", {}),
        variation_points=d.get("variation_points", []),
        assertions=d.get("assertions", {}),
        provenance=d.get("provenance", {}),
        era_budget=d.get("era_budget"),
    )
    validate_seed(seed)
    return seed


def dump_seed(seed: Seed, fmt: str = "yaml") -> str:
    """Serialize a Seed. JSON is byte-fair for machine use."""
    validate_seed(seed)
    if fmt == "json":
        return json.dumps(seed.to_dict(), indent=2, sort_keys=True)
    import yaml
    return yaml.safe_dump(seed.to_dict(), sort_keys=False, allow_unicode=True)
