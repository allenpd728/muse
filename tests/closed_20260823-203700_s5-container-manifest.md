# Test spec — S5 container + manifest (issue #141) — CLOSED

Written by the completing agent per TASK_WORKFLOW step 6. S5 landed with 28
tests (`cd tools/muse_mu && python -m pytest`, <1s).

**Resolution (Tests: #152, 2026-08-23):** all four gaps closed, 36 tests
total. Landed: golden .mu fixture (`tests/fixtures/bwv227.1.minimal.mu`,
740 bytes, verified byte-exact with reproducibility from pinned
FIXTURE_INPUTS); canonicalization adversarial cases (unicode title,
insertion-order independence, whitespace sensitivity); zip metadata
decisions pinned — duplicate member names fail loudly (zipfile.read would
silently return the last entry) and explicit directory entries are layout
noise, not content; real-payload shape (.mu from the actual corpus mxl +
seed yaml, hashes verified).

## Landed coverage (tools/muse_mu/test_manifest.py)

- **Manifest schema:** license enum (three values), attribution/commercial
  types, mandatory ai_involvement value set, unknown-key rejection,
  no-self-hash rule, JSON round-trip, plaintext readability.
- **Container:** write/read round-trip, performances/ accepted, required
  members enforced, unexpected members rejected, non-zip rejected, hash
  mismatch and missing-from-hashes detected on read, write-time hash
  consistency enforced.
- **Signature:** HMAC sign/verify, wrong key fails, tampered title fails,
  unsigned verify raises, signature survives JSON round-trip.
- **Hash primitive:** sha256 empty-vector pin.

## Gaps for a `Tests:` follow-up

1. **Golden .mu fixture.** A committed minimal .mu (bytes) verified by
   CI — the P3 conformance-suite shape; currently the tests build fixtures
   at runtime.
2. **Signature canonicalization adversarial cases.** Unicode in titles,
   nested dict ordering, whitespace in attribution — pin that sign() and
   verify() agree on what counts as "the same manifest".
3. **Zip metadata assumptions.** read_mu trusts zipfile's namelist; pin
   behavior on duplicate member names and directory-entry noise
   (`performances/` as an entry vs implicit) — decide and pin.
4. **Integration with real payloads.** Once S2 (roll) and C1 (seed) emit
   bytes, build a real .mu from corpus + seed and validate it in the
   corpus check gate.

## How to run

```bash
cd tools/muse_mu && python -m pytest
```
