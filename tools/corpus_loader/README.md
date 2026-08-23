# tools/corpus_loader — W2 corpus loader

The ratchet's front door: every downstream tool recovers corpus works
through this loader, never through ad-hoc parsing. Design:
[docs/design/w2-corpus-loader.md](../../docs/design/w2-corpus-loader.md).

## CLI

```bash
python3 tools/corpus_loader/muse_corpus.py list            # registry table
python3 tools/corpus_loader/muse_corpus.py load <work-id>  # IR summary
python3 tools/corpus_loader/muse_corpus.py check           # known-answer gate
python3 tools/corpus_loader/muse_corpus.py update-pins     # re-measure; print drift
```

`check` is the CI gate: exit 0 only if every corpus file parses through the
W1 IR ([tools/ir](../ir/)) and matches its pinned parts/notes/dynamics/
hairpins counts. Exit 1 with a failures list otherwise. Wall-clock budget:
the full gate runs in ~21s here (B9 ≈13s of it); a hard regression beyond a
multiple of that is a smell — investigate before adjusting pins.

`update-pins` re-measures every file and prints drift for human review. Pins
change only by deliberate corpus action; it never rewrites the registry.

## Registry

`WORKS` in `muse_corpus.py` maps the five corpus works (per
[corpus/README.md](../../corpus/README.md)) to their files and
known-answer pins, measured 2026-08-23 through the W1 IR. Pins use the IR's
fidelity contract: every written note event (ties separate, rests/chords/
grace included). New corpus additions must be registered here and in
corpus/README.md.

## Tests

```
cd tools/corpus_loader && python -m pytest
```
