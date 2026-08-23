"""muse_pack — S2 roll encoding (binary layer of S1's event stream).

Columnar channels per part (pitch, onset, duration, voice, velocity,
articulations, notations flags), delta-encoded onsets, dictionary-coded
repeated pitch-patterns, entropy-coded residual via DEFLATE. Round-trips
the corpus losslessly against W4's diff ground truth.
"""

from .pack import pack, unpack

__all__ = ["pack", "unpack"]
