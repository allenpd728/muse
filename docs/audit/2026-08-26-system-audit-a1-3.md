# System audit A1.3 — growth + probes + lineage (run=20260825-1033-cae1)

Modules as one functional unit: muse_grow (harness), muse_probes (compute),
muse_lineage (walker). Verify-and-file; nothing fixed in the audit.

## Known-answer gates

| Gate | Command | Expected | Result | Verdict |
|---|---|---|---|---|
| committed chain walk | `walk(seeds/bwv227.1.v3.seed.yaml)` | `[verified,verified,verified,root]` | exactly that | **works** |
| probes regeneration determinism | `compute_probes(seed, work)` twice | byte-identical report | `to_json` equal | **works** |
| growth harness on G3 fixtures | `compare_deltas(v2, v1)` over `tests/fixtures/bwv227.1.delta.v{1,2}.json` | 5 traits | `[budget_position, mockup_richness, rubato_pstdev_ms, tempo_curve_shape, velocity_pstdev]` | **works** |
| G4 expansion entry shape | `grow_one(work, None)["expansion"]` | 4 keys | `[expansion_time_ms, note_count, operation, variation_point_count]` | **works** |

## Modules

| Module | Doc claim | Evidence | Verdict |
|---|---|---|---|
| muse_grow | no README (finding) | 21 tests green, suite passes | **unpinned (docs)** |
| muse_probes | README describes probe engine gate | README.md present, 36 tests green | **works** |
| muse_lineage | README documents walk/hop/status | README.md present, 12 tests green | **works** |

## Findings (filed)

- muse_grow missing README → #287 (documentation)

## Unit tests

`python3 -m pytest muse_grow muse_probes muse_lineage -q` →
grow 21 + probes 36 + lineage 12 = 69 passed. Full `./tools/run_tests.sh`
green at end of audit.
