"""muse_decode — P1 reference decoder (`.mu` container → event stream).

Reads S5's zip container (manifest + roll.bin + optional performances),
decodes the S2-packed roll via muse_roll, emits the W1 IR event stream.
Deterministic, sandboxed, resource-bounded.
"""

from .decode import decode, DecodeError

__all__ = ["decode", "DecodeError"]
