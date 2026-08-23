"""Chain smoke test (#169): the fast-tier integration gate.

Every registry entry in the fast registry runs the full pipeline
(source → IR → pack → container → decode) with W4 verify PASS; two runs
deterministic; failure names its stage. Registered as a fast-tier smoke
suite in tools/run_tests.sh.
"""

import pytest

from muse_chain import run_work
from muse_chain.chain import check_determinism

FAST_REGISTRY = [
    ("bach-bwv227.1", "bach/bwv227.1.mxl"),
    ("byrd-1-kyrie", "byrd/1-Kyrie.mid"),
    ("byrd-2-gloria", "byrd/2-Gloria.mid"),
]


@pytest.mark.parametrize("wid,rel", FAST_REGISTRY)
def test_chain_smoke_green(wid, rel):
    r = run_work(wid, rel)
    assert r.ok, f"stage failure: {[(s.stage, s.detail) for s in r.stages if s.status == 'FAIL']}"
    verify = next(s for s in r.stages if s.stage.startswith("verify"))
    assert verify.status == "PASS"


def test_chain_smoke_deterministic():
    assert check_determinism(registry=FAST_REGISTRY) == []
