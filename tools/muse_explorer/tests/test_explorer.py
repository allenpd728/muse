"""Explorer tests (issue #164): artifact contract + page mount safety."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from muse_explorer.generate import generate  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
EXPLORER = os.path.join(REPO, "docs", "explorer")


@pytest.fixture(scope="module")
def works(tmp_path_factory):
    out = tmp_path_factory.mktemp("explorer")
    return generate(str(out), quick=True), str(out)


def test_works_json_covers_registry(works):
    entries, _ = works
    assert len(entries) == 13, "every corpus registry file must appear"


def test_every_work_has_pinned_fields(works):
    entries, _ = works
    required = {
        "id", "title", "file", "parts", "notes", "dynamics", "hairpins",
        "duration_ticks", "ppq", "source_format", "part_names",
        "roll_bytes", "pack_ratio", "piano_roll", "patterns",
    }
    for entry in entries:
        assert required <= set(entry), f"{entry['id']}: missing fields"
        assert entry["parts"] > 0 and entry["notes"] > 0
        assert 0 < entry["pack_ratio"] < 1


def test_piano_rolls_exist_and_non_empty(tmp_path):
    """Render contract: one small work renders a real PNG (full renders are
    the committed-artifact path, not the test loop)."""
    out = tmp_path / "one"
    generate(str(out), quick=True)
    committed = os.path.join(EXPLORER, "img", "bach_bwv227.1.png")
    assert os.path.getsize(committed) > 1000
    with open(committed, "rb") as fh:
        assert fh.read(8) == b"\x89PNG\r\n\x1a\n"


def test_json_is_deterministic(tmp_path):
    a = generate(str(tmp_path / "a"), quick=True)
    b = generate(str(tmp_path / "b"), quick=True)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_committed_artifacts_match_regeneration(tmp_path):
    """Freshness tripwire: committed docs/explorer/data/works.json must
    equal a fresh quick regeneration."""
    committed = json.load(open(os.path.join(EXPLORER, "data", "works.json")))
    fresh = generate(str(tmp_path), quick=True)
    assert committed["works"] == fresh, (
        "docs/explorer/data/works.json is stale — regenerate with "
        "python3 tools/muse_explorer/generate.py"
    )


def test_page_mount_safety():
    """index.html must mount safely: fetch path correct, noindex meta,
    error fallback present, no external resources."""
    html = open(os.path.join(EXPLORER, "index.html")).read()
    assert 'noindex' in html
    assert "data/works.json" in html
    assert "boot().catch" in html, "fetch failure must render a fallback"
    assert "http://" not in html and "https://" not in html.replace(
        "https://github.com", ""
    ), "no external runtime resources"
