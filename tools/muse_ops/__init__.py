"""muse_ops — S4 language validator (grammar-only)."""

from .ops import OPS, OpsError, validate_program

__all__ = ["OPS", "OpsError", "validate_program"]
