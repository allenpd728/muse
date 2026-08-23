import json, os, re, random, wave
import numpy as np
import soundfile as sf

SR = 44100
PPQ = 480
DIV = 2
TICKS_PER_DIV = PPQ // DIV
NOTE_OFFSET = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}

def name_to_midi(p):
    p = p.strip().lower()
    letter = p[0]; i = 1; acc = 0
    while i < len(p) and p[i] in '#b':
        acc += 1 if p[i] == '#' else -1
        i += 1
    octave = int(p[i:])
    return 12 * (octave + 1) + NOTE_OFFSET[letter] + acc

def resolve(path):
    if os.path.isfile(path):
        return path
    # case-insensitive per-component walk
    parts = [p for p in path.split(os.sep) if p]
    cur = os.sep
    for comp in parts:
        if os.path.isdir(cur):
            entries = {c.lower(): c for c in os.listdir(cur)}
            cur = os.path.join(cur, entries.get(comp.lower(), comp))
        else:
            cur = os.path.join(cur, comp)
    if os.path.isfile(cur):
        return cur
    # try .flac <-> .wav swap
    for ext in ('.flac', '.wav'):
        alt = os.path.splitext(cur)[0] + ext
        if os.path.isfile(alt):
            return alt
    return cur

def load_wav(path):
    path = resolve(path)
    a, sr = sf.read(path, dtype='float32', always_2d=True)
    a = a.mean(axis=1)
    if sr != SR:
        a = np.interp(np.linspace(0, len(a), int(len(a) * SR / sr)), np.arange(len(a)), a).astype(np.float32)
    return a

def parse_sfz(path):
    base = os.path.dirname(path)
    regions = []
    def parse_file(p, depth=0):
        if depth > 3: return
        text = open(p).read()
        for m in re.finditer(r'#include\s+"([^"]+)"', text):
            parse_file(os.path.normpath(os.path.join(os.path.dirname(p), m.group(1))), depth+1)
        for chunk in text.split('<region>')[1:]:
            r = {}
            for k, v in re.findall(r'(\w+)=([^\n<]+)', chunk):
                r[k] = v.strip()
            if 'sample' in r:
                # SFZ spec: sample paths resolve relative to the TOP-LEVEL sfz
                r['sample'] = os.path.normpath(os.path.join(base, r['sample']))
                regions.append(r)
    parse_file(path)
    return regions

class Instrument:
    def __init__(self, sfz_path):
        self.regions = []
        for r in parse_sfz(sfz_path):
            lo = name_to_midi(r.get('lokey', 'c0'))
            hi = name_to_midi(r.get('hikey', r.get('lokey', 'c8')))
            center = name_to_midi(r.get('pitch_keycenter', r.get('lokey', 'c4')))
            self.regions.append((lo, hi, center, r['sample']))
        self.cache = {}
    def sample_for(self, midi):
        for lo, hi, center, path in self.regions:
            if lo <= midi <= hi:
                return center, path
        # nearest center
        best = min(self.regions, key=lambda r: abs(r[2] - midi))
        return best[2], best[3]
    def note(self, midi, dur_sec, vel, attack_sec=0.02, release_sec=0.4, swell=None):
        center, path = self.sample_for(midi)
        if path not in self.cache:
            rp = resolve(path)
            if not os.path.isfile(rp):
                raise FileNotFoundError(f'sample not found: {path} -> {rp}')
            self.cache[path] = load_wav(path)
        s = self.cache[path]
        ratio = 2 ** ((midi - center) / 12)
        newlen = max(1, int(len(s) / ratio))
        s2 = np.interp(np.linspace(0, len(s), newlen), np.arange(len(s)), s).astype(np.float32)
        n = int(dur_sec * SR) + int(release_sec * SR)
        if len(s2) > n:
            s2 = s2[:n]
        env = np.ones(len(s2), dtype=np.float32)
        atk = max(1, int(attack_sec * SR))
        atk = min(atk, len(s2))
        env[:atk] = np.linspace(0, 1, atk)
        rel = max(1, int(release_sec * SR))
        rel = min(rel, len(s2))
        env[-rel:] *= np.linspace(1, 0, rel)
        if swell:
            pts = np.array(swell, dtype=np.float32)
            x = np.linspace(0, 1, len(s2))
            env *= np.interp(x, pts[:, 0], pts[:, 1])
        return s2 * env * (vel / 127.0) * 0.35

def bpm_curve(tempo_map, total_divs):
    pts = [(t['division'], t['bpm']) for t in tempo_map]
    pts.append((total_divs, pts[-1][1]))
    return pts

def div_to_sec(pts, div):
    sec = 0.0
    for i in range(len(pts) - 1):
        d0, bpm = pts[i]; d1, _ = pts[i+1]
        if div <= d0: break
        seg_end = min(div, d1)
        sec += (seg_end - d0) / 2.0 * 60.0 / bpm  # 2 divisions per quarter
        if div <= d1: break
    return sec

def render(score_path, mockup_path, inst_paths, out_path, mechanical=False):
    score = json.load(open(score_path))
    mockup = json.load(open(mockup_path)) if mockup_path else None
    rng = random.Random(42)
    total_divs = max(n['onset'] + n['duration'] for notes in score['parts'].values() for n in notes)
    parts = list(score['parts'].keys())
    insts = [Instrument(p) for p in inst_paths]

    # compute real end time: last note's actual rendered end + release tail
    note_mods_all = {}
    inner_all = {}
    if mockup and not mechanical and 'notes' in mockup:
        inner_all = mockup['notes'].get('inner_voices', {})
        for pk, v in mockup['notes'].items():
            if isinstance(v, list):
                note_mods_all[pk] = {m['i']: m for m in v if isinstance(m, dict) and 'i' in m}
    ends = []
    for part in parts:
        for idx, n in enumerate(score['parts'][part]):
            if mechanical:
                on_sec = n['onset'] / 2.0 * 60.0 / 72
                dur_sec = n['duration'] / 2.0 * 60.0 / 72
                rel = 0.4
            else:
                pts = bpm_curve(mockup['tempo_map'], total_divs)
                mod = note_mods_all.get(part, {}).get(idx, {})
                on_sec = div_to_sec(pts, n['onset']) + mod.get('onset_offset_ticks', 0) / PPQ * 60.0 / 72
                dur_scale = mod.get('duration_scale', 1.0)
                off_sec = div_to_sec(pts, n['onset'] + n['duration'])
                dur_sec = (off_sec - div_to_sec(pts, n['onset'])) * dur_scale
                dur_sec += mod.get('legato_overlap_ms', inner_all.get('legato_overlap_ms', 0)) / 1000.0
                rel = mod.get('release_sec', 0.4)
            ends.append(on_sec + dur_sec + rel)
    total_sec = max(ends) + 0.1
    buf = np.zeros(int(total_sec * SR), dtype=np.float32)

    for pi, part in enumerate(parts):
        gain = 1.0
        if mockup and not mechanical:
            for b in mockup['balance']:
                if b['part'] == part: gain = b['gain']
        note_mods = {}
        inner = {}
        if mockup and not mechanical and 'notes' in mockup:
            if part in mockup['notes']:
                note_mods = {m['i']: m for m in mockup['notes'][part] if isinstance(m, dict) and 'i' in m}
            inner = mockup['notes'].get('inner_voices', {})
        for idx, n in enumerate(score['parts'][part]):
            midi = name_to_midi(n['pitch'])
            mod = note_mods.get(idx, {})
            if mechanical:
                on_sec = n['onset'] / 2.0 * 60.0 / 72
                dur_sec = n['duration'] / 2.0 * 60.0 / 72
                vel = 77
                jitter = 0.0
                attack_sec, release_sec, swell = 0.02, 0.4, None
            else:
                pts = bpm_curve(mockup['tempo_map'], total_divs)
                offset_ticks = mod.get('onset_offset_ticks', 0)
                on_sec = div_to_sec(pts, n['onset']) + offset_ticks / PPQ * 60.0 / 72
                dur_scale = mod.get('duration_scale', 1.0)
                off_sec = div_to_sec(pts, n['onset'] + n['duration'])
                dur_sec = (off_sec - div_to_sec(pts, n['onset'])) * dur_scale
                overlap_ms = mod.get('legato_overlap_ms', inner.get('legato_overlap_ms', 0))
                dur_sec += overlap_ms / 1000.0
                lvl = mockup['dynamics'][0]['level']
                for d in mockup['dynamics']:
                    if d['division'] <= n['onset']: lvl = d['level']
                vel = mod.get('velocity', int(lvl * gain * 100))
                vel = max(20, min(110, vel))
                jitter = rng.uniform(0, 0.015) if part in ('alto', 'tenor') and not mod else 0.0
                attack_sec = mod.get('attack_sec', 0.05)
                release_sec = mod.get('release_sec', 0.4)
                swell = mod.get('swell', inner.get('swell'))
            start = int((on_sec + jitter) * SR)
            s = insts[pi % len(insts)].note(midi, dur_sec, vel, attack_sec, release_sec, swell)
            end = min(len(buf), start + len(s))
            buf[start:end] += s[:end - start]

    # gentle stereo widen + soft clip
    buf = np.tanh(buf)
    stereo = np.stack([buf, buf], axis=1)
    out = (stereo * 32767).astype(np.int16)
    w = wave.open(out_path, 'wb')
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(out.tobytes()); w.close()
    print('wrote', out_path, f'{len(buf)/SR:.1f}s')

SSO = '/tmp/sso/sso-master/Sonatina Symphonic Orchestra/Strings - Performance'
insts = [
    f'{SSO}/Violin Solo 1 Sustain.sfz',
    f'{SSO}/Violin Solo 2 Sustain.sfz',
    f'{SSO}/Viola Solo Legato.sfz',
    f'{SSO}/Cello Solo Legato.sfz',
]
render('/tmp/chorale-phrase.json', None, insts, '/tmp/chorale-mech-sso.wav', mechanical=True)
render('/tmp/chorale-phrase.json', '/tmp/mockup-v1.json', insts, '/tmp/chorale-mockup-sso.wav', mechanical=False)
render('/tmp/chorale-phrase.json', '/tmp/mockup-v2.json', insts, '/tmp/chorale-mockup-v2-sso.wav', mechanical=False)
