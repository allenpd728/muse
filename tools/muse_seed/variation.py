"""S3.4 variation points — named regions where interpretation may vary.

A variation point marks a tick region of the work with a kind (what may
happen there), a budget (how much, 0..1 of the region's material), and
attached assertions evaluated by muse_assert (S3.5). Regions are IR ticks,
matching the work's ppq — the same space the analyzer and diff tool use.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class VariationError(ValueError):
    """Raised when a variation point violates the S3.4 schema."""


KINDS = frozenset({
    "ornament",      # added notes within the region (trills, turns, passing)
    "repeat",        # optional repeat of the region
    "cadenza",       # extended free insertion at the region boundary
    "ossia",         # alternative reading of the region
    "tempo_flex",    # local tempo freedom beyond the global budget
})

# Assertion kinds a variation point may attach (delegated to muse_assert).
ATTACHABLE_ASSERTIONS = frozenset({
    "must_contain", "register", "form", "tempo_bounds",
})


@dataclass(frozen=True)
class VariationPoint:
    start_tick: int
    end_tick: int
    kind: str
    budget: float = 0.2            # 0..1 fraction of region material
    assertions: dict = field(default_factory=dict)
    label: str = ""

    def validate(self):
        if self.start_tick < 0:
            raise VariationError(f"negative start_tick {self.start_tick}")
        if self.end_tick <= self.start_tick:
            raise VariationError(
                f"region must be non-empty: [{self.start_tick}, {self.end_tick})")
        if self.kind not in KINDS:
            raise VariationError(f"unknown kind {self.kind!r} (known: {sorted(KINDS)})")
        if not (0.0 <= self.budget <= 1.0):
            raise VariationError(f"budget {self.budget} outside [0, 1]")
        if not isinstance(self.assertions, dict):
            raise VariationError("assertions must be a mapping")
        unknown = set(self.assertions) - ATTACHABLE_ASSERTIONS
        if unknown:
            raise VariationError(
                f"unattachable assertion kinds: {sorted(unknown)} "
                f"(attachable: {sorted(ATTACHABLE_ASSERTIONS)})")

    def to_dict(self):
        d = {
            "region": [self.start_tick, self.end_tick],
            "kind": self.kind,
            "budget": self.budget,
            "assertions": dict(self.assertions),
        }
        if self.label:
            d["label"] = self.label
        return d

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise VariationError("variation point must be a mapping")
        unknown = set(d) - {"region", "kind", "budget", "assertions", "label"}
        if unknown:
            raise VariationError(f"unknown keys: {sorted(unknown)}")
        region = d.get("region")
        if (not isinstance(region, list) or len(region) != 2
                or not all(isinstance(t, int) for t in region)):
            raise VariationError("region must be [start_tick, end_tick] ints")
        if "kind" not in d:
            raise VariationError("kind is required")
        vp = cls(
            start_tick=region[0],
            end_tick=region[1],
            kind=d["kind"],
            budget=d.get("budget", 0.2),
            assertions=d.get("assertions", {}),
            label=d.get("label", ""),
        )
        vp.validate()
        return vp


def validate_variation_points(points: list, duration_ticks: int | None = None):
    """Validate a seed's variation_points list. With duration_ticks, also
    assert every region lands inside the work (and warn-free ordering)."""
    if not isinstance(points, list):
        raise VariationError("variation_points must be a list")
    parsed = [VariationPoint.from_dict(p) if isinstance(p, dict) else p for p in points]
    for vp in parsed:
        if not isinstance(vp, VariationPoint):
            raise VariationError(f"variation point must be a mapping, got {type(vp).__name__}")
        vp.validate()
    ordered = sorted(parsed, key=lambda v: (v.start_tick, v.end_tick))
    for a, b in zip(ordered, ordered[1:]):
        if b.start_tick < a.end_tick:
            raise VariationError(
                f"overlapping regions [{a.start_tick}, {a.end_tick}) and "
                f"[{b.start_tick}, {b.end_tick}) — split or merge them")
    if duration_ticks is not None:
        for vp in parsed:
            if vp.end_tick > duration_ticks:
                raise VariationError(
                    f"region [{vp.start_tick}, {vp.end_tick}) exceeds work "
                    f"duration {duration_ticks}")
    return parsed
