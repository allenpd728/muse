"""B5 appendix + asks (issue #267; spec tests/open_20260825-120000_b5-appendix-asks.md).

Source-scan tier: appendix covers P3/D20/D7/D11 with correct substance,
the asks page lists the three asks with anchors, and the meta-D20 test —
the page about confidentiality must not itself leak mockup content.
"""

import os

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
APPENDIX = os.path.join(REPO, "docs", "boardroom", "appendix.html")
ASKS = os.path.join(REPO, "docs", "boardroom", "asks.html")


def _read(path):
    with open(path) as fh:
        return fh.read()


class TestAppendix:
    def test_covers_the_four_topics(self):
        text = _read(APPENDIX)
        assert "conformance" in text.lower() and "golden vector" in text.lower()
        assert "never leaves the pipeline" in text          # D20 substance
        assert "No model training" in text                   # D7 substance
        assert "ear gates quality" in text                   # D11 substance

    def test_decision_anchors(self):
        text = _read(APPENDIX)
        for anchor in ("D20", "D7", "D11"):
            assert anchor in text

    def test_meta_d20_no_leak(self):
        # the page about confidentiality must not itself carry mockup data
        text = _read(APPENDIX)
        assert ".mockup.json" not in text
        assert '"tempo_map"' not in text
        assert "onset_offset_ms" not in text


class TestAsks:
    def test_three_asks_with_anchors(self):
        text = _read(ASKS)
        assert "event-first" in text                        # ask 1
        assert "open-at-launch" in text and "D4" in text    # ask 2
        assert "publication-surface" in text and "#211" in text  # ask 3

    def test_read_only(self):
        for path in (APPENDIX, ASKS):
            assert "<form" not in _read(path).lower()
