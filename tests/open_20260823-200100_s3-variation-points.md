# Test spec — S3.4 variation points (issue #145)

Written by the completing agent per TASK_WORKFLOW step 6. S3.4 landed with
22 tests (`cd tools/muse_seed && python -m pytest`, <1s; 42 total in the
package with S3.3's).

## Landed coverage (tools/muse_seed/test_variation.py)

- **Schema:** all five kinds accepted; unknown kind/keys rejected; region
  shape enforced ([start, end] ints); kind required; empty/negative regions
  rejected; budget bounds [0, 1]; attachable vs unattachable assertion
  kinds; dict round-trip lossless.
- **List validation:** overlapping regions rejected, adjacency accepted,
  work-bounds check against duration_ticks, non-list/non-mapping rejected.
- **Integration:** `validate_seed()` fails the whole seed on a bad
  variation point; empty list stays optional.

## Gaps for a `Tests:` follow-up

1. **Assertion evaluation against a real performance.** S3.4 pins the
   schema; evaluating an attached assertion (e.g. register within an
   ornament region) against an actual mockup is muse_assert's path — pin
   one end-to-end case (seed + region + mockup violating the register
   assertion → AssertionError naming the region).
2. **Kind semantics per kind.** The schema accepts all five kinds, but
   what a cadenza vs. an ossia *means* for the mockup harness (L1) is
   unspecified — pin semantic fixtures when L1 consumes them.
3. **Budget calibration link.** budget is schema-checked only (0..1);
   C3's era budgets should eventually bound suggested defaults per kind —
   test the suggestion path once C3 lands.

## How to run

```bash
cd tools/muse_seed && python -m pytest
```
