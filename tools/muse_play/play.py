"""muse_play — P2 reference renderer (issue #198).

Event stream (S1) → audio, soundfont tier (FluidSynth-class with GM
fallback). The renderer-side proof of the S1 contract; the seam L2 lives
above. Offline playback only — no streaming, no DAW.

Renders via the same envelope-at-pitch path as L2's muse_render, reading
from the S1 stream (Work) rather than the mockup. CLI exposes
`muse play <source>` for MusicXML/MIDI corpus sources and `.mu` containers.

IR path note: muse_ir is imported lazily inside functions so pytest's
package-level collection does not require IR path injection before this
module's import.
"""

from __future__ import annotations

import math
import wave

import numpy as np

SR = 44100


def _ir():
    from muse_ir import load
    return load


class PlayError(Exception):
    pass


def _midi_to_freq(pitch: int) -> float:
    return 440.0 * 2 ** ((pitch - 69) / 12.0)


def _ticks_to_sec(tick: int, tempo_map: list, ppq: int = 480) -> float:
    sec = 0.0
    last_tick, last_bpm = 0, 120
    for mtick, mbpm in sorted(tempo_map or [(0, 120000)]):
        bpm = mbpm / 1000.0
        if tick <= mtick:
            break
        sec += (mtick - last_tick) * 60.0 / (last_bpm * ppq)
        last_tick, last_bpm = mtick, bpm
    sec += (tick - last_tick) * 60.0 / (last_bpm * ppq)
    return sec


def render_work(work, out_path: str) -> dict:
    """Event stream → WAV via envelope at pitch frequency."""
    work.validate()
    ppq = work.meta.ppq
    max_end = 0.0
    events = []
    for part in work.parts:
        for n in part.notes:
            if n.pitch is None or getattr(n, "is_rest", False) or getattr(n, "is_unpitched", False):
                continue
            onset_sec = _ticks_to_sec(n.onset, work.maps.tempo, ppq)
            dur_sec = _ticks_to_sec(n.onset + n.duration, work.maps.tempo, ppq) - onset_sec
            max_end = max(max_end, onset_sec + dur_sec)
            events.append((onset_sec, dur_sec, n.pitch, n.velocity or 60))
    if not events:
        raise PlayError("no pitched notes to render")
    max_end += 0.5
    buf = np.zeros(int(max_end * SR), dtype=np.float32)
    for onset_sec, dur_sec, pitch, velocity in events:
        n = max(1, int(dur_sec * SR))
        t = np.arange(n, dtype=np.float32) / SR
        freq = _midi_to_freq(pitch)
        env = np.ones(n, dtype=np.float32)
        a = min(0.01, n * 0.2 / SR)
        d = min(0.05, n * 0.2 / SR)
        ka = int(a * SR)
        kd = int(d * SR)
        if ka > 0:
            env[:ka] = np.linspace(0, 1, ka, dtype=np.float32)
        if 0 < kd < n:
            env[-kd:] *= np.linspace(1, 0, kd, dtype=np.float32)
        amp = (velocity / 127.0) * 0.2
        wave_ = np.sin(2 * math.pi * freq * t) * env * amp
        i0 = int(onset_sec * SR)
        i1 = min(len(buf), i0 + n)
        buf[i0:i1] += wave_[: i1 - i0]
    peak = np.abs(buf).max()
    if peak > 1.0:
        buf = buf / peak
    _write_wav(out_path, buf)
    return {"out": out_path, "duration_sec": round(max_end, 3), "notes": len(events), "parts": len(work.parts)}


def play(source: str, out_path: str = None) -> dict:
    """Convenience wrapper: source file (MusicXML/MIDI) → WAV."""
    work = _ir()(source)
    out = out_path or source.replace(os.path.splitext(source)[1], ".wav")
    return render_work(work, out)


def _write_wav(path: str, samples: np.ndarray):
    s16 = (samples * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(s16.tobytes())
