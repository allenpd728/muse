"""Seed model + validation for S3.1 container & encoding."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


class SeedError(ValueError):
    """Raised when a seed violates the S3.1 schema."""


TOP_LEVEL_KEYS = {
    "format_version", "work_id", "title", "params", "philosophy",
    "variation_points", "assertions", "provenance",
}

REQUIRED_KEYS = {"format_version", "work_id", "params", "assertions"}


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

    def to_dict(self):
        return {
            "format_version": self.format_version,
            "work_id": self.work_id,
            "title": self.title,
            "params": self.params,
            "philosophy": self.philosophy,
            "variation_points": self.variation_points,
            "assertions": self.assertions,
            "provenance": self.provenance,
        }


def validate_seed(seed: Seed):
    """S3.1 schema checks. Fail loudly on unknown/missing keys."""
    missing = REQUIRED_KEYS - {
        k for k, v in seed.to_dict().items() if v or k in ("format_version", "work_id")
    }
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
    if seed.philosophy:
        from .philosophy import Philosophy, PhilosophyError

        try:
            Philosophy.from_dict(seed.philosophy)
        except PhilosophyError as e:
            raise SeedError(f"philosophy: {e}") from e


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
