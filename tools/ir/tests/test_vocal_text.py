"""Vocal text in the IR (S6, issue #318).

The Ninth's finale is texted — the corpus file carries 3,588 <lyric>
elements — and before this the IR had no field for any of it, so the format
could carry the notes but not the words while the pipeline gate claimed
"the score reconstructs the source losslessly".

These tests pin the carrier (lyric/syllabic/extend on Note), the parsing,
and the property that actually matters: a word split across notes rejoins
into the text the composer set.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from muse_ir import load  # noqa: E402
from muse_ir.model import (  # noqa: E402
    KNOWN_SYLLABIC, IRValidationError, Meta, Note, Part, Work,
)

from conftest import corpus_path  # noqa: E402

B9 = ("beethoven", "beethoven-sym9.xml")
# Works with no vocal text — must stay unaffected.
INSTRUMENTAL = [
    ("bach", "bwv227.1.mxl"),
    ("schubert", "death-and-the-maiden.mxl"),
    ("beethoven", "beethoven-sym5-mov1.xml"),
]


@pytest.fixture(scope="module")
def b9():
    return load(corpus_path(*B9))


def lyric_notes(work):
    return [n for p in work.parts for n in p.notes if n.lyric is not None]


# --- parsing the real corpus ---

def test_b9_lyric_counts(b9):
    """Known-answer pins against the source XML: 3,588 <lyric> elements, of
    which one is a bare <extend> (no text), giving 3,587 texted notes."""
    notes = lyric_notes(b9)
    assert len(notes) == 3587
    assert sum(1 for p in b9.parts for n in p.notes if n.extend) == 405


def test_syllabic_vocabulary_is_the_known_four(b9):
    values = {n.syllabic for n in lyric_notes(b9)}
    assert values <= KNOWN_SYLLABIC, values
    assert values == {"single", "begin", "middle", "end"}


def test_words_reconstruct_across_notes(b9):
    """The property the carrier exists for. MusicXML splits a word across
    notes (`begin`/`middle`/`end`); rejoining them must reproduce the text
    the composer set, not just the syllables in isolation.

    This is the assertion that would fail if syllabic were dropped or
    mis-ordered — counts alone would still pass.
    """
    words, current = [], ""
    for n in lyric_notes(b9):
        if n.syllabic == "begin":
            current = n.lyric
        elif n.syllabic == "middle":
            current += n.lyric
        elif n.syllabic == "end":
            words.append(current + n.lyric)
            current = ""
        elif n.syllabic == "single":
            words.append(n.lyric)
    assert current == "", f"unterminated word at end of work: {current!r}"
    assert words[:8] == [
        "Wer", "ein", "holdes", "Weib", "errungen,", "mische", "seinen", "Jubel",
    ], words[:8]
    assert len(words) == 2074, len(words)
    joined = " ".join(words)
    assert "Freude, schöner Götterfunken" in joined, joined[:200]


def test_melisma_extends_a_syllable(b9):
    """`<extend>` marks a syllable held over later notes. In B9 every extend
    accompanies its own text; the parser keeps a *standalone* extend as
    extend-only (lyric=None), which this pins both ways."""
    extended = [n for p in b9.parts for n in p.notes if n.extend]
    assert extended, "no melismas found — the corpus changed?"
    assert all(n.lyric is not None for n in extended), (
        "B9's extends all carry text; a None lyric here means the parser "
        "mis-assigned an extend"
    )


@pytest.mark.parametrize("parts", INSTRUMENTAL)
def test_instrumental_works_carry_no_lyrics(parts):
    """The new fields must default cleanly for every non-texted work, so the
    change is additive rather than a new obligation on existing sources."""
    work = load(corpus_path(*parts))
    assert lyric_notes(work) == []
    assert all(not n.extend and n.syllabic is None
               for p in work.parts for n in p.notes)


# --- validation ---

def test_unknown_syllabic_is_rejected():
    work = Work(
        parts=[Part(id="P1", name="P1", notes=[
            Note(pitch=60, onset=0, duration=10, lyric="Freu", syllabic="bogus"),
        ])],
        meta=Meta(source_format="musicxml", ppq=480),
    )
    with pytest.raises(IRValidationError, match="unknown syllabic"):
        work.validate()


def test_empty_string_lyric_is_rejected():
    """A bare <extend/> means "the previous syllable continues", so the parser
    emits lyric=None. An empty-string lyric would count as a texted note and
    corrupt word reconstruction, so it must never be stored."""
    work = Work(
        parts=[Part(id="P1", name="P1", notes=[
            Note(pitch=60, onset=0, duration=10, lyric=""),
        ])],
        meta=Meta(source_format="musicxml", ppq=480),
    )
    with pytest.raises(IRValidationError, match="empty-string lyric"):
        work.validate()


def test_lyric_is_part_of_the_deterministic_sort():
    """Two notes identical in every musical respect but differing in text
    must still order deterministically (otherwise `validate`'s sortedness
    check is unstable for texted works)."""
    a = Note(pitch=60, onset=0, duration=10, lyric="a")
    b = Note(pitch=60, onset=0, duration=10, lyric="b")
    assert sorted([b, a], key=lambda n: n.sort_key()) == [a, b]
    work = Work(
        parts=[Part(id="P1", name="P1", notes=sorted([b, a], key=lambda n: n.sort_key()))],
        meta=Meta(source_format="musicxml", ppq=480),
    )
    work.validate()  # must not raise


# --- parser edge cases ---

def test_additional_verses_are_carried(tmp_path):
    """Multi-verse is real corpus evidence (bwv227.7 and bwv227.11 set two
    texts per note), so verse 2 is carried, not dropped.

    This test previously asserted the *opposite* — that verse 2 was dropped
    with a warning — on the mistaken belief that "only verse 1 is used in the
    corpus". Checking the chorales disproved that: a Lutheran chorale sings
    one tune to several texts, so discarding verse 2 would lose half the words.
    """
    xml = """<?xml version="1.0"?>
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>Voice</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration>
        <lyric number="1"><syllabic>single</syllabic><text>Freude</text></lyric>
        <lyric number="2"><syllabic>single</syllabic><text>Joy</text></lyric>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    path = tmp_path / "two-verses.xml"
    path.write_text(xml, encoding="utf-8")
    work = load(str(path))
    notes = lyric_notes(work)
    assert len(notes) == 1
    assert notes[0].lyric == "Freude"
    assert [(v.number, v.lyric) for v in notes[0].verses] == [(2, "Joy")]


def test_corpus_multiverse_chorales_keep_both_verses():
    """The evidence for the design: both Bach movements that set two verses
    per note carry both after parsing, and verse 2 is a *different* text."""
    for movement in ("bwv227.7.mxl", "bwv227.11.mxl"):
        work = load(corpus_path("bach", movement))
        v1 = [n.lyric for n in work.parts[0].notes if n.lyric]
        v2 = [v.lyric for n in work.parts[0].notes for v in n.verses if v.lyric]
        assert len(v1) == 38, (movement, len(v1))
        assert len(v2) == 17, (movement, len(v2))
        assert v1[:2] == ["Je", "su,"], (movement, v1[:2])
        assert "".join(v2[:4]) != "".join(v1[:4]), (
            f"{movement}: verse 2 should be different words, not a repeat"
        )


def test_unknown_syllabic_warns_and_keeps_the_text(tmp_path):
    xml = """<?xml version="1.0"?>
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>Voice</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration>
        <lyric number="1"><syllabic>composite</syllabic><text>Freude</text></lyric>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    path = tmp_path / "odd-syllabic.xml"
    path.write_text(xml, encoding="utf-8")
    work = load(str(path))
    notes = lyric_notes(work)
    assert len(notes) == 1 and notes[0].lyric == "Freude"
    assert notes[0].syllabic is None
    assert any("syllabic" in w for w in work.meta.warnings), work.meta.warnings


def test_bare_extend_carries_no_text(tmp_path):
    xml = """<?xml version="1.0"?>
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>Voice</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration>
        <lyric number="1"><extend/></lyric>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    path = tmp_path / "extend-only.xml"
    path.write_text(xml, encoding="utf-8")
    work = load(str(path))
    # <extend/> with no <text> is the melisma marker on a note the syllable
    # already covers; it must not surface as an empty lyric.
    assert all(n.lyric != "" for p in work.parts for n in p.notes)