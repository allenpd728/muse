# muse_seed — S3.1 container & encoding

Seed bytes reader/writer + validator per
[docs/design/s3-seed-format/SPEC.md](../../docs/design/s3-seed-format/SPEC.md).

## Usage

```python
from muse_seed import Seed, load_seed, dump_seed, validate_seed

seed = load_seed(yaml_text, fmt="yaml")
dump_seed(seed, fmt="json")   # byte-fair machine encoding
validate_seed(seed)           # raises SeedError on schema violation
```

Top-level keys: format_version, work_id, title, params, philosophy,
variation_points, assertions, provenance. Required: format_version,
work_id, params, assertions.

## S3.2 — Parameters + ranges (params.py)

Era-calibrated budgets from delta-analysis:

```python
from muse_seed.params import tempo_budget, velocity_budget, chord_spread_ms

tempo_budget("classical", 96)   # TempoRange(62..129, default 96)
velocity_budget("romantic")     # 1.45 (145% spread)
chord_spread_ms("baroque")      # 16
```

Eras: baroque, classical, romantic, early_romantic. All ranges validate
(TempoRange, EnergyRange, DensityRange, VariationRange).

## S3.3 — Philosophy fields (philosophy.py)

Typed-lite vocabulary with free-text escape; provenance required:

```python
from muse_seed.philosophy import Philosophy, PhilosophyError

Philosophy.from_dict({
    "tempo_philosophy": ["flexible", "architectural"],   # vocab or free-text
    "provenance": {"author": "founder", "ai_assisted": False},
})
```

Fields: tempo_philosophy, dynamic_philosophy, articulation_stance,
ornamentation_stance, ensemble_stance. The identity guard enforces the
no-artist-lookalikes rule: any capitalized name-like phrase requires
`provenance.license_ref`; era phrases ("Venetian School") pass as styles.
Wired into `validate_seed()` — a bad philosophy block fails the whole seed.

## S3.4 — Variation points (variation.py)

Named regions where interpretation may vary:

```python
from muse_seed.variation import VariationPoint, validate_variation_points

VariationPoint.from_dict({
    "region": [480, 960], "kind": "ornament", "budget": 0.2,
    "assertions": {"register": {"part": "soprano", "min": "C4", "max": "A5"}},
})
```

Kinds: ornament, repeat, cadenza, ossia, tempo_flex. Regions are IR ticks,
half-open, non-overlapping; `validate_variation_points(points,
duration_ticks=...)` bounds-checks against the loaded work. Attached
assertions are S3.5's kinds, evaluated by `muse_assert`. Wired into
`validate_seed()`.

## Tests

```
cd tools/muse_seed && python -m pytest
```
