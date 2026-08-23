"""S2 roll encoding — lossless packing of the W1 IR.

Format (FORMAT_SPEC §4.6): header + varint-coded columnar streams. Onsets
and map ticks delta-encoded; repeated (pitch, duration, velocity) cells
dictionary-coded; articulations and notations dictionary-coded; the whole
payload zlib-compressed (entropy coding, stdlib).

Lossless against the source IR, proven by W4 (recall = precision = 1.0 on
every corpus file).
"""

from __future__ import annotations

import json
import struct
import zlib

from muse_ir.model import (
    DynamicMarking,
    Hairpin,
    Instrument,
    Maps,
    Meta,
    Note,
    Part,
    Work,
)

MAGIC = b"MUR1"


class RollError(ValueError):
    """Raised on malformed roll bytes or unsupported payloads."""


# ---- varint primitives ----

def _uv(n: int) -> bytes:
    """Unsigned varint (7-bit little-endian groups, MSB = continuation)."""
    if n < 0:
        raise RollError(f"unsigned varint of negative {n}")
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _sv(n: int) -> bytes:
    """Signed varint (zigzag)."""
    return _uv((n << 1) ^ (n >> 63) if n >= 0 else ((-n) << 1) - 1)


class _Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def uv(self) -> int:
        shift = 0
        value = 0
        while True:
            if self.pos >= len(self.data):
                raise RollError("truncated varint")
            b = self.data[self.pos]
            self.pos += 1
            value |= (b & 0x7F) << shift
            if not b & 0x80:
                return value
            shift += 7
            if shift > 70:
                raise RollError("varint too long")

    def sv(self) -> int:
        n = self.uv()
        return (n >> 1) if n & 1 == 0 else -((n + 1) >> 1)

    def take(self, n: int) -> bytes:
        if self.pos + n > len(self.data):
            raise RollError("truncated payload")
        chunk = self.data[self.pos:self.pos + n]
        self.pos += n
        return chunk


# ---- string table ----

def _pack_str(s: str) -> bytes:
    b = s.encode("utf-8")
    return _uv(len(b)) + b


def _read_str(r: _Reader) -> str:
    return r.take(r.uv()).decode("utf-8")


# ---- encode ----

def encode(work: Work) -> bytes:
    """Work → roll.bin bytes. Deterministic."""
    work.validate()
    strings: list = []
    sidx: dict = {}

    def S(s):
        if s not in sidx:
            sidx[s] = len(strings)
            strings.append(s)
        return sidx[s]

    parts_buf = bytearray()
    for part in work.parts:
        parts_buf += _pack_part(part, S)

    maps_buf = bytearray()
    maps_buf += _uv(len(work.maps.tempo))
    prev = 0
    for tick, mbpm in work.maps.tempo:
        maps_buf += _sv(tick - prev) + _uv(mbpm)
        prev = tick
    maps_buf += _uv(len(work.maps.meter))
    prev = 0
    for tick, num, den in work.maps.meter:
        maps_buf += _sv(tick - prev) + _uv(num) + _uv(den)
        prev = tick
    maps_buf += _uv(len(work.maps.key))
    prev = 0
    for tick, fifths, mode in work.maps.key:
        maps_buf += _sv(tick - prev) + _sv(fifths) + _uv(S(mode))
        prev = tick

    meta = {
        "source_format": work.meta.source_format,
        "ppq": work.meta.ppq,
        "title": work.meta.title,
        "warnings": list(work.meta.warnings),
    }
    meta_b = json.dumps(meta, sort_keys=True, separators=(",", ":")).encode()

    strings_b = b"".join(_pack_str(s) for s in strings)
    payload = (
        _uv(len(strings)) + strings_b
        + _uv(len(meta_b)) + meta_b
        + bytes(maps_buf)
        + _uv(len(work.parts)) + bytes(parts_buf)
    )
    blob = zlib.compress(payload, 9)
    return MAGIC + _uv(len(blob)) + blob


def _pack_part(part: Part, S) -> bytes:
    out = bytearray()
    out += _pack_str(part.id) + _pack_str(part.name)
    instr = part.instrument
    flags = (instr.name is not None) | ((instr.gm_program is not None) << 1)
    out += _uv(flags)
    if instr.name is not None:
        out += _pack_str(instr.name)
    if instr.gm_program is not None:
        out += _uv(instr.gm_program)
    out += _uv(1 if part.inferred_voice else 0)

    out += _uv(len(part.notes))
    prev_onset = 0
    for n in part.notes:
        out += _sv(n.onset - prev_onset)
        prev_onset = n.onset
        # presence bitmap: pitch, velocity, articulations, notations, source_id
        pres = (
            (n.pitch is not None)
            | ((n.velocity is not None) << 1)
            | (bool(n.articulations) << 2)
            | (bool(n.notations) << 3)
            | ((n.source_id is not None) << 4)
        )
        out += _uv(pres)
        if n.pitch is not None:
            out += _uv(n.pitch)
        out += _uv(n.duration)
        out += _uv(n.voice)
        if n.velocity is not None:
            out += _uv(n.velocity)
        out += _uv(1 if n.velocity_inferred else 0)
        if n.articulations:
            out += _uv(len(n.articulations))
            for a in n.articulations:
                out += _uv(S(a))
        if n.notations:
            out += _uv(len(n.notations))
            for f in sorted(n.notations):
                out += _uv(S(f))
        if n.source_id is not None:
            out += _pack_str(n.source_id)

    out += _uv(len(part.dynamics))
    prev = 0
    for d in part.dynamics:
        out += _sv(d.tick - prev) + _uv(S(d.text))
        prev = d.tick

    out += _uv(len(part.hairpins))
    prev = 0
    for h in part.hairpins:
        out += _sv(h.start_tick - prev)
        prev = h.start_tick
        out += _uv(1 if h.end_tick is not None else 0)
        if h.end_tick is not None:
            out += _uv(h.end_tick - h.start_tick)
        out += _uv(S(h.kind))
    return bytes(out)


# ---- decode ----

def decode(data: bytes) -> Work:
    """roll.bin bytes → Work. Fails loudly on malformed input."""
    if not isinstance(data, (bytes, bytearray)) or len(data) < 8:
        raise RollError("not a roll payload")
    if bytes(data[:4]) != MAGIC:
        raise RollError(f"bad magic {bytes(data[:4])!r}")
    r = _Reader(bytes(data[4:]))
    plen = r.uv()
    payload = r.take(plen)
    try:
        raw = zlib.decompress(payload)
    except zlib.error as e:
        raise RollError(f"zlib payload corrupt: {e}") from e
    pr = _Reader(raw)

    strings = [_read_str(pr) for _ in range(pr.uv())]

    def S(i):
        if not 0 <= i < len(strings):
            raise RollError(f"string-table index {i} out of range")
        return strings[i]

    meta = json.loads(pr.take(pr.uv()).decode())

    maps = Maps()
    prev = 0
    for _ in range(pr.uv()):
        tick = prev + pr.sv()
        maps.tempo.append((tick, pr.uv()))
        prev = tick
    prev = 0
    for _ in range(pr.uv()):
        tick = prev + pr.sv()
        maps.meter.append((tick, pr.uv(), pr.uv()))
        prev = tick
    prev = 0
    for _ in range(pr.uv()):
        tick = prev + pr.sv()
        maps.key.append((tick, pr.sv(), S(pr.uv())))
        prev = tick

    parts = [_read_part(pr, S) for _ in range(pr.uv())]
    if pr.pos != len(raw):
        raise RollError("trailing bytes in payload")

    return Work(
        parts=parts,
        maps=maps,
        meta=Meta(
            source_format=meta["source_format"],
            ppq=meta["ppq"],
            title=meta.get("title"),
            warnings=list(meta.get("warnings", [])),
        ),
    )


def _read_part(pr: _Reader, S) -> Part:
    pid = _read_str(pr)
    name = _read_str(pr)
    flags = pr.uv()
    instr = Instrument(
        name=_read_str(pr) if flags & 1 else None,
        gm_program=pr.uv() if flags & 2 else None,
    )
    inferred = bool(pr.uv())

    notes = []
    prev_onset = 0
    for _ in range(pr.uv()):
        onset = prev_onset + pr.sv()
        prev_onset = onset
        pres = pr.uv()
        pitch = pr.uv() if pres & 1 else None
        duration = pr.uv()
        voice = pr.uv()
        velocity = pr.uv() if pres & 2 else None
        velocity_inferred = bool(pr.uv())
        articulations = tuple(S(pr.uv()) for _ in range(pr.uv())) if pres & 4 else ()
        notations = frozenset(S(pr.uv()) for _ in range(pr.uv())) if pres & 8 else frozenset()
        source_id = _read_str(pr) if pres & 16 else None
        notes.append(Note(
            pitch=pitch, onset=onset, duration=duration, voice=voice,
            velocity=velocity, velocity_inferred=velocity_inferred,
            articulations=articulations, notations=notations, source_id=source_id,
        ))

    dynamics = []
    prev = 0
    for _ in range(pr.uv()):
        tick = prev + pr.sv()
        dynamics.append(DynamicMarking(tick=tick, text=S(pr.uv())))
        prev = tick

    hairpins = []
    prev = 0
    for _ in range(pr.uv()):
        start = prev + pr.sv()
        prev = start
        has_end = pr.uv()
        end = start + pr.uv() if has_end else None
        hairpins.append(Hairpin(kind=S(pr.uv()), start_tick=start, end_tick=end))

    return Part(id=pid, name=name, instrument=instr, notes=notes,
                dynamics=dynamics, hairpins=hairpins, inferred_voice=inferred)


def verify_round_trip(work: Work) -> bool:
    """encode → decode → structural equality, the W4 pre-check."""
    other = decode(encode(work))
    return _canonical(work) == _canonical(other)


def _canonical(work: Work) -> dict:
    return {
        "meta": (work.meta.source_format, work.meta.ppq, work.meta.title,
                 tuple(work.meta.warnings)),
        "maps": (tuple(work.maps.tempo), tuple(work.maps.meter), tuple(work.maps.key)),
        "parts": tuple(
            (p.id, p.name, (p.instrument.name, p.instrument.gm_program),
             p.inferred_voice,
             tuple((n.pitch, n.onset, n.duration, n.voice, n.velocity,
                    n.velocity_inferred, tuple(n.articulations),
                    tuple(sorted(n.notations)), n.source_id) for n in p.notes),
             tuple((d.tick, d.text) for d in p.dynamics),
             tuple((h.kind, h.start_tick, h.end_tick) for h in p.hairpins))
            for p in work.parts
        ),
    }
