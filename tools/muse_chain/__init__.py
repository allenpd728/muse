"""muse_chain — E2E chain harness (#162).

Lazy re-exports: conftest may need to insert sibling paths (tools/ir)
before the chain module is importable.
"""

_LAZY = {
    "REGISTRY": "chain",
    "ChainResult": "chain",
    "StageResult": "chain",
    "check_determinism": "chain",
    "run_all": "chain",
    "run_work": "chain",
}

__all__ = list(_LAZY)


def __getattr__(name):
    if name in _LAZY:
        from . import chain

        return getattr(chain, name)
    raise AttributeError(name)
