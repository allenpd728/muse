# Benchmark corpus

Canonical public-domain scores imported to `.muse.json` via the Batch 2
importer (`node importer/cli.mjs <source> -o <out>`). The corpus is the
yardstick for interpreter/player conformance (vision doc: "the benchmark is
the scoreboard") and doubles as the importer's large-scale test corpus.

## Traditions

| Tradition | Entries | What it stresses |
|---|---|---|
| **Bach chorales** (SATB, homophonic) | 6 | Motif recall across transposed phrases, form fidelity in strict periodic structure, additive rhythm cells, key signatures with accidentals |
| **Haydn string quartet** (Op. 74 No. 1, 4 movements) | 4 | Longer forms, mid-piece key/tempo changes, contrapuntal part independence, movement-scale structure |

## Entries

| File | Source | Tradition | Notes |
|---|---|---|---|
| `bwv26.6.muse.json` | Bach, BWV 26.6 (music21 corpus) | chorale | opening key signature stress |
| `bwv269.muse.json` | Bach, BWV 269 (music21 corpus) | chorale | G major, dotted rhythms; also the importer's own fixture piece |
| `bwv292.muse.json` | Bach, BWV 292 (music21 corpus) | chorale | |
| `bwv316.muse.json` | Bach, BWV 316 (music21 corpus) | chorale | |
| `bwv331.muse.json` | Bach, BWV 331 (music21 corpus) | chorale | |
| `bwv344.muse.json` | Bach, BWV 344 (music21 corpus) | chorale | extra inference entry (4 inferred) |
| `haydn_op74n1_movement1.muse.json` | Haydn, Op. 74 No. 1 "The Horse", mvt 1 (music21 corpus) | string quartet | largest file; parser needed raised heap (see note) |
| `haydn_op74n1_movement2.muse.json` | Haydn, Op. 74 No. 1, mvt 2 | string quartet | |
| `haydn_op74n1_movement3.muse.json` | Haydn, Op. 74 No. 1, mvt 3 | string quartet | menuet + trio form |
| `haydn_op74n1_movement4.muse.json` | Haydn, Op. 74 No. 1, mvt 4 | string quartet | parser needed raised heap (see note) |

## Provenance

- All sources are public-domain scores from the
  [music21 corpus](https://github.com/cuthbertLab/music21/tree/master/music21/corpus)
  (`.mxl` compressed MusicXML), kept under `sources/` for re-import.
- Every `.muse.json` records its import in `metadata.provenance`
  (`event: "import"`, `ai: false`) per the scope doc; heuristic inferences
  (motif extraction, section detection) are marked in
  `extensions.importer.inferred`.
- All 10 files pass `node tools/validate.mjs` against `schema/muse.schema.json`.

## Known limitation: parser memory scaling

Movements 1 and 4 exceed the default Node heap during motif extraction
(OOM at ~4 GB); re-import with `node --max-old-space-size=8192` (mvt 1) or
`--max-old-space-size=16384` (mvt 4). This is a scaling gap in
`importer/synthesize.mjs` for large scores, not a correctness bug — file a
task if corpus growth hits it routinely.

## Adding entries

1. Drop the source (`.mxl`/`.musicxml`/`.mid`) in `sources/`.
2. `node importer/cli.mjs sources/<file> -o <name>.muse.json`
   (raise `--max-old-space-size` for large scores).
3. `node tools/validate.mjs <name>.muse.json` must pass.
4. Add a row to the table above, noting what the entry stresses.
