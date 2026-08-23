import os

import pytest

CORPUS_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "corpus")
)


def corpus_path(*parts):
    path = os.path.join(CORPUS_ROOT, *parts)
    if not os.path.exists(path):
        pytest.skip(f"corpus file missing: {path}")
    return path
