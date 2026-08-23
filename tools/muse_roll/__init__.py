"""muse_roll — S2 roll encoding (lossless IR packing).

Lazy re-exports: conftest may need to insert sibling paths (tools/ir)
before the codec module is importable.
"""

_LAZY = {
    "MAGIC": "roll",
    "RollError": "roll",
    "decode": "roll",
    "encode": "roll",
    "verify_round_trip": "roll",
}

__all__ = list(_LAZY)


def __getattr__(name):
    if name in _LAZY:
        from . import roll

        return getattr(roll, name)
    raise AttributeError(name)
