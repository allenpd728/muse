"""E2 venue-plan doc coherence (issue #230; spec
tests/open_20260824-103353_e2-venue-plan.md).

The deliverable is a document, so coverage is mechanical coherence: the
plan keeps satisfying #210's DoD, and the three status caches (design
doc, design index, pipeline) don't drift apart. Pure text assertions —
no fixtures, no network. Match on stable keywords, not full lines, so
rewording that keeps meaning does not over-pin.
"""

import os
import re

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOC = os.path.join(REPO, "docs", "design", "e2-the-venue.md")
INDEX = os.path.join(REPO, "docs", "design", "index.md")
PIPELINE = os.path.join(REPO, "docs", "pipeline.md")


def _read(path):
    with open(path) as fh:
        return fh.read()


def _section(doc_text, heading_keyword):
    """Slice a '## <heading>' section by keyword until the next '## '."""
    m = re.search(rf"^## .*{re.escape(heading_keyword)}.*$", doc_text, re.MULTILINE | re.IGNORECASE)
    assert m, f"no '## ...{heading_keyword}...' heading"
    rest = doc_text[m.end():]
    nxt = re.search(r"^## ", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


# --- Behavior 1: DoD sections present ---

def test_dod_sections_present():
    text = _read(DOC)
    for keyword in ("Venue option", "Staging mechanics", "Projection design", "Provenance + rights"):
        assert re.search(rf"^## .*{re.escape(keyword)}", text, re.MULTILINE), (
            f"docs/design/e2-the-venue.md lost its '## {keyword}' section"
        )


# --- Behavior 2: plan content pins ---

def test_venue_section_names_a_recommendation():
    venue = _section(_read(DOC), "Venue option")
    assert re.search(r"[Rr]ecommend", venue), "venue section lost its recommendation"
    assert re.search(r"\d+\s*[–-]\s*\d+\s*seats", venue), "venue section lost its capacity pin"


def test_staging_addresses_deliberation_pacing():
    staging = _section(_read(DOC), "Staging mechanics")
    assert "deliberation" in staging.lower(), "staging section no longer addresses live deliberation"


def test_rights_section_references_manifest_conventions():
    rights = _section(_read(DOC), "Provenance + rights")
    assert "ai_involvement" in rights, "rights section lost the manifest ai_involvement reference"
    assert re.search(r"[Nn]o artist lookalikes", rights), "rights section lost the no-lookalikes rule"


# --- Behavior 3: three-cache status coherence ---

PROMOTED = re.compile(r"draft|done|final|in[- ]progress", re.IGNORECASE)
STALE = re.compile(r"\bscaffold\b|\bfiled\b", re.IGNORECASE)


def _e2_row(text):
    m = re.search(r"\| E2 — The venue \|.*", text)
    assert m, "E2 row not found"
    return m.group(0)


def test_status_caches_agree():
    doc = _read(DOC)
    index_row = _e2_row(_read(INDEX))
    pipeline_row = _e2_row(_read(PIPELINE))

    doc_status = re.search(r"Status: ([^*]+)\*\*", doc)
    assert doc_status, "design doc lost its Status: line"
    doc_state = doc_status.group(1)

    for name, surface in (("design doc", doc_state), ("design index", index_row), ("pipeline", pipeline_row)):
        assert not STALE.search(surface), f"{name} regressed to scaffold/filed: {surface!r}"
        assert PROMOTED.search(surface), f"{name} shows no promoted state: {surface!r}"
        assert "#210" in surface, f"{name} lost the #210 reference: {surface!r}"


# --- Behavior 4: downstream E3 contract intact ---

def test_e3_non_goals_explicit():
    non_goals = _section(_read(DOC), "Scope")
    assert re.search(r"[Nn]on-goals", non_goals), "Scope section lost its Non-goals"
    assert re.search(r"[Bb]roadcast", non_goals), "broadcast/distribution no longer out of scope"


def test_recording_rights_requirement_retained():
    rights = _section(_read(DOC), "Provenance + rights")
    assert re.search(r"[Vv]enue agreement", rights), "venue-agreement requirement dropped"
    assert re.search(r"[Ee]3", rights), "E3 downstream dependency no longer named"
    assert re.search(r"[Rr]ecording", rights), "recording rights no longer required"
