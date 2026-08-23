"""S3.3 philosophy fields — typed-lite vocabulary + free-text escape.

Performance philosophy declares *how* a work may be brought to life:
style/era/practice references in a closed vocabulary, plus a free-text
escape for anything the vocabulary doesn't cover. The ground rule binds
here: philosophies reference styles and practices, never an artist's
identity, without an explicit license recorded in provenance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


class PhilosophyError(ValueError):
    """Raised when a philosophy block violates the S3.3 vocabulary."""


FIELDS = frozenset({
    "tempo_philosophy",
    "dynamic_philosophy",
    "articulation_stance",
    "ornamentation_stance",
    "ensemble_stance",
})

# Typed-lite: the known vocabulary. Free-text is the sanctioned escape
# (any non-empty string not in this set), so this list may grow without
# breaking existing seeds — additive only.
VOCABULARY = frozenset({
    # tempo
    "flexible", "architectural", "strict", "rubato", "dance-pulse",
    # dynamics
    "terraced", "dramatic", "restrained", "hairpin-led",
    # articulation
    "consort", "breathe-at-cadences", "detached", "legato-led", "rhetorical",
    # ornamentation
    "sparse", "improvised", "written-out", "none",
    # ensemble
    "soloistic", "blended", "antiphonal",
})

# Identity guard: any capitalized name-like phrase ("Firstname Lastname")
# is treated as a suspected artist identity and requires an explicit
# license in provenance. Era/style adjectives ("Viennese Classical") are
# whitelisted as eras, not identities.
_IDENTITY_HINT = re.compile(r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b")

ERA_PHRASES = frozenset({
    "Viennese Classical", "Second Viennese", "Ars Nova", "Ars Subtilior",
    "North German", "South German", "New German", "Galant Style",
    "Stile Antico", "Stile Moderno", "Notre Dame", "English Madrigal",
    "Flemish School", "Roman School", "Venetian School", "Mannheim School",
})


@dataclass
class Philosophy:
    """One work's philosophy block. Fields are FIELDS; values are typed
    vocabulary entries or free-text strings."""

    entries: dict = field(default_factory=dict)  # field -> list[str]
    provenance: dict = field(default_factory=dict)  # author, license_ref?, ai_assisted

    def validate(self):
        unknown = set(self.entries) - FIELDS
        if unknown:
            raise PhilosophyError(f"unknown philosophy fields: {sorted(unknown)}")
        if not self.entries:
            raise PhilosophyError("philosophy block is empty")
        for name, values in self.entries.items():
            if not isinstance(values, list) or not values:
                raise PhilosophyError(f"{name}: must be a non-empty list")
            for v in values:
                if not isinstance(v, str) or not v.strip():
                    raise PhilosophyError(f"{name}: entries must be non-empty strings")
                self._check_identity(name, v)
        self._validate_provenance()

    def _check_identity(self, field_name, value):
        """Artist-identity references need an explicit license."""
        for match in _IDENTITY_HINT.findall(value):
            if match in ERA_PHRASES:
                continue
            if not self.provenance.get("license_ref"):
                raise PhilosophyError(
                    f"{field_name}: suspected artist identity {match!r} requires "
                    f"provenance.license_ref (no artist lookalikes without license)"
                )

    def _validate_provenance(self):
        if not self.provenance.get("author"):
            raise PhilosophyError("provenance.author is required")
        ai = self.provenance.get("ai_assisted")
        if ai is None:
            raise PhilosophyError("provenance.ai_assisted is required (AI disclosure)")
        if not isinstance(ai, bool):
            raise PhilosophyError("provenance.ai_assisted must be a boolean")

    def to_dict(self):
        """Flat mapping: philosophy fields at top level, provenance nested —
        the same shape a seed's philosophy block carries."""
        d = {k: list(v) for k, v in self.entries.items()}
        d["provenance"] = dict(self.provenance)
        return d

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise PhilosophyError("philosophy must be a mapping")
        entries = {k: v for k, v in d.items() if k != "provenance"}
        prov = d.get("provenance", {})
        p = cls(entries=entries, provenance=prov)
        p.validate()
        return p
