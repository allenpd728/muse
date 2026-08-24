"""muse_distill — L4 distiller: mockup → seed revision."""

from .distill import Interpretation, dump_delta, extract_interpretation, seed_revision

__all__ = ["Interpretation", "extract_interpretation", "seed_revision", "dump_delta"]
