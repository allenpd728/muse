"""muse_seed — S3.1 container & encoding (seed bytes reader/writer).

Top-level seed schema per docs/design/s3-seed-format/SPEC.md. YAML for
author-editability; JSON encoding for machine use. Byte-fair round-trip.
"""

from .seed import Seed, load_seed, dump_seed, validate_seed, SeedError

__all__ = ["Seed", "load_seed", "dump_seed", "validate_seed", "SeedError"]
