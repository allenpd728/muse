"""muse_diff — W4 diff tool.

IR ↔ IR comparison: recall/precision in tick space, tolerance-configurable.
The ground truth for every compression claim and every conformance vector.
"""

from .diff import diff, DiffReport, Mismatch

__all__ = ["diff", "DiffReport", "Mismatch"]
