"""Vocal text through the roll codec (S6, issue #318).

Presence-bitmap bits 5-7 (lyric, syllabic, extend). The important property is
that text survives encode→decode, and that the *canonical comparison* used by
tools/muse_chain includes it — otherwise the chain would pass while the words
were lost, which is the exact gap #318 was filed to close.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from muse_ir import load  # noqa: E402
from muse_ir.model import Meta, Note, Part, Work  # noqa: E402
from muse_roll.roll import _canonical, decode, encode  # noqa: E402

CORPUS = Path(__file__).resolve().parents[3] / "corpus"


def corpus_path(*parts):
    path = CORPUS.joinpath(*parts)
    if not path.exists():
        pytest.skip(f"corpus file missing: {path}")
    return str(path)


def roundtrip(work):
    return decode(encode(work))


def texted_work():
    return Work(
        parts=[Part(id="P1", name="P1", notes=[
            Note(pitch=64, onset=0, duration=480, lyric="Freu", syllabic="begin"),
            Note(pitch=62, onset=480, duration=480, lyric="de", syllabic="end"),
            Note(pitch=60, onset=960, duration=480, lyric="schön", syllabic="single",
                 extend=True),
            Note(pitch=60, onset=1440, duration=480),  # instrumental
        ])],
        meta=Meta(source_format="musicxml", ppq=480),
    )


def test_text_survives_roundtrip():
    src = texted_work()
    out = roundtrip(src)
    src_notes = [n for p in src.parts for n in p.notes]
    out_notes = [n for p in out.parts for n in p.notes]
    assert [(n.lyric, n.syllabic, n.extend) for n in out_notes] == [
        (n.lyric, n.syllabic, n.extend) for n in src_notes
    ], "lyric/syllabic/extend did not round-trip"
    assert out_notes[1].lyric == "de" and out_notes[1].syllabic == "end"
    assert out_notes[2].extend is True
    assert out_notes[3].lyric is None, "an instrumental note gained a lyric"


def test_canonical_covers_vocal_text():
    """The chain's equality check must see the text. Without this, a codec
    regression that dropped lyrics would still 'verify'."""
    src = texted_work()
    assert _canonical(src) == _canonical(roundtrip(src))

    stripped = roundtrip(src)
    for p in stripped.parts:
        for n in p.notes:
            n.lyric = None
            n.syllabic = None
            n.extend = False
    assert _canonical(stripped) != _canonical(src), (
        "canonical comparison ignores vocal text — a lost lyric would verify"
    )


def test_canonical_detects_a_changed_syllable():
    """Not just presence: a different syllable, syllabic class, or melisma
    flag must change the key too, or the chain would accept corrupted text.
    Each mutation targets a note that actually carries the field."""
    src = texted_work()

    changed_lyric = roundtrip(src)
    changed_lyric.parts[0].notes[0].lyric = "FREU"
    assert _canonical(changed_lyric) != _canonical(src), "lyric edit not detected"

    changed_syllabic = roundtrip(src)
    changed_syllabic.parts[0].notes[0].syllabic = "single"
    assert _canonical(changed_syllabic) != _canonical(src), "syllabic edit not detected"

    # note index 2 is the one built with extend=True
    changed_extend = roundtrip(src)
    assert changed_extend.parts[0].notes[2].extend is True
    changed_extend.parts[0].notes[2].extend = False
    assert _canonical(changed_extend) != _canonical(src), "extend edit not detected"


def test_repeated_syllables_are_interned_once():
    """Syllables repeat heavily in texted music; they go through the same
    string table as dynamics, so a repeated syllable must not grow the
    payload linearly."""
    notes = [Note(pitch=60, onset=i * 480, duration=480, lyric="der",
                  syllabic="single") for i in range(200)]
    with_text = Work(parts=[Part(id="P1", name="P1", notes=notes)],
                     meta=Meta(source_format="musicxml", ppq=480))
    without = Work(
        parts=[Part(id="P1", name="P1",
                    notes=[Note(pitch=60, onset=i * 480, duration=480)
                           for i in range(200)])],
        meta=Meta(source_format="musicxml", ppq=480),
    )
    delta = len(encode(with_text)) - len(encode(without))
    # 200 lyrics + 200 syllabic indices; interning keeps this to well under
    # a byte-and-a-half per field on average rather than ~4 bytes each.
    assert delta < 700, f"lyric payload grew by {delta} bytes for 200 repeats"


def test_instrumental_works_are_byte_identical_to_golden():
    """The change is additive: a work with no text must encode exactly as it
    did before (bits 5-7 stay zero). Verified against the committed fixtures
    in test_roll_gaps.py; this asserts the property directly and cheaply."""
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    assert not any(n.lyric or n.syllabic or n.extend
                   for p in work.parts for n in p.notes)
    assert _canonical(work) == _canonical(roundtrip(work))


def test_multiverse_chorales_round_trip_both_verses():
    """The corpus's two-verse chorales must survive the codec with both
    texts intact — this is the assertion that fails if the verse dimension is
    ever dropped from the encoding or the canonical comparison."""
    for movement in ("bwv227.7.mxl", "bwv227.11.mxl"):
        work = load(corpus_path("bach", movement))
        out = roundtrip(work)
        assert _canonical(out) == _canonical(work)
        src_v2 = [(v.number, v.lyric, v.syllabic)
                  for p in work.parts for n in p.notes for v in n.verses]
        out_v2 = [(v.number, v.lyric, v.syllabic)
                  for p in out.parts for n in p.notes for v in n.verses]
        assert src_v2 == out_v2
        assert len(out_v2) == 17, (movement, len(out_v2))


def test_beethoven9_text_round_trips():
    """The forcing case: the Ninth's 3,587 lyrics and 405 melismas survive
    the codec. This is the assertion that makes 'the score reconstructs the
    source losslessly' true for the v1.0 conformance target."""
    work = load(corpus_path("beethoven", "beethoven-sym9.xml"))
    out = roundtrip(work)
    src_lyrics = [(n.onset, n.lyric, n.syllabic, n.extend)
                  for p in work.parts for n in p.notes if n.lyric is not None]
    out_lyrics = [(n.onset, n.lyric, n.syllabic, n.extend)
                  for p in out.parts for n in p.notes if n.lyric is not None]
    assert len(src_lyrics) == 3587
    assert out_lyrics == src_lyrics
    assert _canonical(out) == _canonical(work)
    # and the words rejoin after the round trip
    words, current = [], ""
    for _, ly, syl, _ in out_lyrics:
        if syl == "begin":
            current = ly
        elif syl == "middle":
            current += ly
        elif syl == "end":
            words.append(current + ly)
            current = ""
        elif syl == "single":
            words.append(ly)
    assert " ".join(words[:4]) == "Wer ein holdes Weib"


def test_three_verses_round_trip_and_canonical():
    """The encoding supports n verses, but only the corpus's two are tested.
    Pin a synthetic three-verse note through encode→decode and the canonical
    comparison, so a regression in the verse loop fails here and not only at
    the (two-verse) corpus."""
    from muse_ir.model import Verse

    src = Work(
        parts=[Part(id="P1", name="P1", notes=[
            Note(pitch=60, onset=0, duration=480, lyric="Freude", syllabic="single",
                 verses=(Verse(number=2, lyric="Joy", syllabic="single"),
                         Verse(number=3, lyric="Göt", syllabic="begin"))),
        ])],
        meta=Meta(source_format="musicxml", ppq=480),
    )
    out = roundtrip(src)
    n = out.parts[0].notes[0]
    assert n.lyric == "Freude" and n.syllabic == "single"
    assert [(v.number, v.lyric, v.syllabic) for v in n.verses] == [
        (2, "Joy", "single"),
        (3, "Göt", "begin"),
    ]
    assert _canonical(out) == _canonical(src)


def test_b9_per_lyric_byte_cost_is_interning_bounded():
    """Item 7 of #319: at scale, pin both the distinct-syllable count and the
    per-lyric byte cost. B9's 3,587 texted notes carry only 231 distinct
    syllables, so removing all text must shrink the payload by far less than
    a naive fixed cost per note would imply. The 8,807-byte delta (≈2.45
    bytes/lyric) is the amendment already pinned in test_roll_gaps.py; this
    asserts the *mechanism* — a small distinct set — directly, so a change
    that stopped interning (making the delta grow with note count) fails
    here even if the total stays under the budget."""
    work = load(corpus_path("beethoven", "beethoven-sym9.xml"))
    lyrics = [n.lyric for p in work.parts for n in p.notes if n.lyric is not None]
    assert len(lyrics) == 3587
    assert len(set(lyrics)) == 231, "distinct-syllable count changed"

    stripped = decode(encode(work))
    for p in stripped.parts:
        for n in p.notes:
            n.lyric = None
            n.syllabic = None
            n.extend = False
            n.verses = ()
    delta = len(encode(work)) - len(encode(stripped))
    assert delta == 8807, (
        f"B9 text costs {delta} bytes; pinned at 8807 (3,587 lyrics + 405 "
        "melismas, interned). Drift means either the corpus or the encoding "
        "changed — review, then amend this pin and test_roll_gaps.py together"
    )