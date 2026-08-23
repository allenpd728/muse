# Test spec — S3.3 philosophy fields (issue #144)

Written by the completing agent per TASK_WORKFLOW step 6. S3.3 landed with
20 tests (`cd tools/muse_seed && python -m pytest`, <1s).

## Landed coverage (tools/muse_seed/test_philosophy.py)

- **Vocabulary:** typed values accepted; free-text escape accepted; unknown
  field / empty block / empty list / blank string all rejected loudly.
- **Identity guard:** artist-identity phrases ("Glenn Gould", "Johann
  Sebastian Bach") require `provenance.license_ref`; era phrases (schools,
  periods) pass as styles; the guard is a name-shape heuristic, not a
  blocklist.
- **Provenance:** author required; ai_assisted required and must be boolean;
  license_ref unlocks identity references.
- **Integration:** `validate_seed()` (S3.1) fails the whole seed on a bad
  philosophy block; philosophy remains optional (absent block passes);
  dict round-trip is lossless.

## Gaps for a `Tests:` follow-up

1. **Identity-guard adversarial sweep.** The heuristic catches "Firstname
   Lastname" capitalized phrases and whitelists 15 era phrases. Test
   hyphenated names ("Beethoven-adjacent"), lowercase impersonations
   ("like bach"), three-name identities, and non-English school names;
   document whether the guard needs a locale table or a case-folding pass.
2. **YAML path coverage.** load_seed(fmt="yaml") ran in the S3.1 suite; the
   philosophy validator via YAML text should be pinned there once PyYAML is
   a declared dependency somewhere (currently only JSON is dependency-free).
3. **Vocabulary drift contract.** VOCABULARY is additive-only per the spec
   decision log — no test yet pins that removing a term breaks (a deliberate
   spec-evolution tripwire).

## How to run

```bash
pip install pyyaml   # only needed by S3.1's YAML path
cd tools/muse_seed && python -m pytest
```
