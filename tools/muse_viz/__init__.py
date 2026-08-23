"""muse_viz — W5 visualizer.

IR + optional pattern report → piano-roll plots with overlays. Founder
review aid. matplotlib; 52-part-safe via part selection and thinning.
"""

from .render import render, PianoRollConfig

__all__ = ["render", "PianoRollConfig"]
