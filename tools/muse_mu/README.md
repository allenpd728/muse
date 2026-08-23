# muse_mu — S5 container + manifest

`.mu` zip layout and the plaintext rights manifest, per
[FORMAT_SPEC §7.1](../../FORMAT_SPEC.md) and
[docs/design/s5-container-manifest.md](../../docs/design/s5-container-manifest.md).

## Usage

```python
from muse_mu import build_manifest, write_mu, read_mu

m = build_manifest(
    work_id="bwv227.1",
    license={"renditions": "open-within-constraints",
             "attribution": "J.S. Bach, public domain",
             "commercial": False},
    provenance={"source": "corpus/bach/bwv227.1.mxl",
                "author": "founder", "ai_involvement": "assisted"},
    members={"roll.bin": roll_bytes, "seed.bin": seed_bytes},
)
write_mu("work.mu", m, {"roll.bin": roll_bytes, "seed.bin": seed_bytes})

manifest, members = read_mu("work.mu")      # verifies hashes by default
manifest.sign(b"key"); manifest.verify(b"key")  # optional HMAC signature
```

Required members: `manifest.json`, `roll.bin`, `seed.bin`; optional:
`performances/*.perf`. Hashes are SHA-256 of every member; the manifest
never hashes itself. Signature is optional HMAC-SHA256 over canonical JSON
(PKI deferred).

## Tests

```
cd tools/muse_mu && python -m pytest
```
