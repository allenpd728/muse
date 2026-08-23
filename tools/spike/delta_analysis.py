import glob, os, sys
import numpy as np
import mido

BASE = '/tmp/v4x22/vienna4x22_rematched-master'

def perf_data(path):
    mid = mido.MidiFile(path)
    tempo_events = [(0, 500000)]
    for msg in mid.merged_track:
        if msg.is_meta and msg.type == 'set_tempo':
            tempo_events.append((msg.time, msg.tempo))
    tempo_events.sort()
    def tick_to_sec(tick):
        sec = 0.0
        last_tick, last_tempo = 0, 500000
        for t, tempo in tempo_events[1:]:
            if tick <= t: break
            sec += (t - last_tick) / mid.ticks_per_beat * last_tempo / 1e6
            last_tick, last_tempo = t, tempo
        sec += (tick - last_tick) / mid.ticks_per_beat * last_tempo / 1e6
        return sec
    out = []
    active = {}
    abs_tick = 0
    for msg in mid.merged_track:
        abs_tick += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            active[msg.note] = (abs_tick, msg.velocity)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in active:
                on, vel = active.pop(msg.note)
                out.append((tick_to_sec(on), tick_to_sec(abs_tick), msg.note, vel))
    out.sort()
    return out

def analyze(pattern, label):
    perfs = sorted(glob.glob(f'{BASE}/midi/{pattern}'))
    rows = []
    for p in perfs:
        notes = perf_data(p)
        onsets = np.array([n[0] for n in notes])
        vels = np.array([n[3] for n in notes])
        pid = os.path.basename(p).replace('.mid','').split('_')[-1]
        total = onsets[-1] - onsets[0]
        spreads = []
        i = 0
        while i < len(onsets):
            j = i
            while j < len(onsets) and onsets[j] - onsets[i] < 0.03:
                j += 1
            if j - i > 1:
                spreads.append((onsets[j-1] - onsets[i]) * 1000)
            i = j
        rows.append((pid, total, vels.mean(), vels.std(), np.mean(spreads) if spreads else 0, notes))
    durs = np.array([r[1] for r in rows])
    vels = np.array([r[2] for r in rows])
    vstds = np.array([r[3] for r in rows])
    spreads = np.array([r[4] for r in rows if r[4] > 0])
    print(f"\n=== {label} ({len(rows)} pianists) ===")
    print(f"duration       : min {durs.min():.1f}s | max {durs.max():.1f}s | spread {(durs.max()/durs.min()-1)*100:.0f}%")
    print(f"mean velocity  : min {vels.min():.0f} | max {vels.max():.0f} | spread {(vels.max()/vels.min()-1)*100:.0f}%")
    print(f"velocity std   : mean {vstds.mean():.1f} (within-performance dynamic range)")
    print(f"chord spread   : mean {spreads.mean():.0f}ms | range {spreads.min():.0f}-{spreads.max():.0f}ms")
    return rows

if __name__ == '__main__':
    analyze('Mozart_K331_1st-mov_p*.mid', 'Mozart K.331 bars 1-18 (Classical)')
    analyze('Chopin_op10_no3_p*.mid', 'Chopin op.10 no.3 bars 1-21 (Romantic)')
    analyze('Schubert_D783_no15_p*.mid', 'Schubert D.783 no.15 (early Romantic)')
    analyze('Chopin_op38_p*.mid', 'Chopin Ballade op.38 bars 1-45 (Romantic)')
