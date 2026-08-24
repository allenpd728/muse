# tools/muse_event — E1 execution scaffold

Deterministic scaffold for the event chain per issue #200: the corpus
ladder (Bach → Byrd → Schubert → Beethoven 5 mov1 → Beethoven 9) through
the concert-quality work. The stage tooling all exists (author, mockup,
assert, render); this scaffold runs the chain and writes an event-ledger
per ladder rung.

## CLI

```
python -m muse_event [--era classical] [--out event_dir]
```

## API

```python
from muse_event import LADDER, event_chain, run_ladder
result = run_ladder("event_dir")
r = event_chain(source, work_id, rung, out_dir, era="classical")
```

## Ladder (pinned)

1. Bach BWV227.1
2. Byrd Kyrie
3. Schubert D.810
4. Beethoven Symphony 5, mvt 1
5. Beethoven Symphony 9

## Tests

```
cd tools/muse_event && python -m pytest
```

4 tests: ladder covered, chain callable, ledger shape symmetric, rungs ok.
The founder's-ear gate stays in the front; this scaffold executes the
chain it autor.
