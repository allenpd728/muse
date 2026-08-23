# Test spec — S2 roll encoding (issue #138)

Written by the completing agent per TASK_WORKFLOW step 6. S2 landed with 31
tests (`cd tools/muse_roll && python -m pytest`, ~2.4s).

## Landed coverage (tools/muse_roll/test_roll.py)

- **Varint primitives:** unsigned/signed round-trips across magnitudes,
  negative unsigned rejected, truncated varint loud.
- **Round-trips:** synthetic work exercising every codec path (rests,
  unpitched, grace, ties, articulations, unicode title, warnings, hairpin
  with open end, instrument fields, multi-map works); deterministic encode;
  Bach/Byrd/Schubert/B5 corpus round-trips lossless.
- **Malformed inputs:** bad magic, truncated payload, corrupt zlib,
  non-bytes, dangling string-table index — all RollError.
- **CLI:** pack → verify LOSSLESS (W4 gate), tampered roll fails, unpack
  summary.
- **Corpus gate (out-of-band, this session):** all 13 files lossless —
  12/13 via W4 verify; B9 structurally (encode→decode→canonical compare,
  168 KB from 68.8 MB, encode 0.8s).

## Gaps for a `Tests:` follow-up

1. **B9 W4 verify.** The pairwise diff on 239k events is the slow path;
   either budget-pin it (background/nightly) or add a sampled-verify mode
   to the gate. The codec itself is sub-second.
2. **Golden roll vectors.** Commit .roll.bin fixtures for the small works
   (Bach, Byrd) so format changes fail byte-exact comparison, not just
   round-trip — the S1 golden-vector pattern, applied to R1.
3. **Format-version tripwire.** MUR1 has no version field beyond the
   magic; if R2 ever lands, pin that old magic still decodes (or fails
   with a version error, not corruption).
4. **Size regression budget.** Ratios are documented in the README; pin
   per-file ratio ceilings in the suite so a packing regression fails CI.

## How to run

```bash
cd tools/muse_roll && python -m pytest
python3 tools/muse_roll/cli.py verify corpus/bach/bwv227.1.mxl <roll>
```
