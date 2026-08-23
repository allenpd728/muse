import json, random
import mido

PPQ = 480
DIV = 2  # divisions per quarter in source
TICKS_PER_DIV = PPQ // DIV

PITCH_MAP = {}
NOTE_OFFSET = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

def pitch_to_midi(p):
    letter = p[0]
    i = 1
    acc = 0
    while i < len(p) and p[i] in '#b':
        acc += 1 if p[i] == '#' else -1
        i += 1
    octave = int(p[i:])
    return 12 * (octave + 1) + NOTE_OFFSET[letter] + acc

def bpm_at(tempo_map, div):
    bpm = tempo_map[0]['bpm']
    for pt in tempo_map:
        if pt['division'] <= div:
            bpm = pt['bpm']
    return bpm

def level_at(dynamics, div):
    lvl = dynamics[0]['level']
    for pt in dynamics:
        if pt['division'] <= div:
            lvl = pt['level']
    return lvl

def build(score_path, mockup_path, out_path, mechanical=False):
    score = json.load(open(score_path))
    mockup = json.load(open(mockup_path)) if mockup_path else None
    rng = random.Random(42)

    mid = mido.MidiFile(ticks_per_beat=PPQ)
    tempo_track = mido.MidiTrack()
    mid.tracks.append(tempo_track)
    tempo_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(72), time=0))

    # events: (abs_tick, msg)
    events = []
    for part, notes in score['parts'].items():
        gain = 1.0
        if mockup and not mechanical:
            for b in mockup['balance']:
                if b['part'] == part:
                    gain = b['gain']
        for n in notes:
            div_on = n['onset']
            div_off = n['onset'] + n['duration']
            if mechanical:
                bpm_on = bpm_off = 72
                level = 0.6
                jitter = 0
                dur_scale = 1.0
            else:
                bpm_on = bpm_at(mockup['tempo_map'], div_on)
                bpm_off = bpm_at(mockup['tempo_map'], div_off)
                level = level_at(mockup['dynamics'], div_on)
                jitter = rng.randint(0, 8) if part in ('alto', 'tenor') else 0
                dur_scale = 1.0
                # phrase-final lengthening: notes ending on long durations
                if n['duration'] >= 4:
                    dur_scale = 1.1
            tick_on = div_on * TICKS_PER_DIV + jitter
            tick_off = tick_on + int(n['duration'] * TICKS_PER_DIV * dur_scale)
            vel = int(level * gain * 100)
            vel = max(20, min(110, vel))
            ch = ['soprano', 'alto', 'tenor', 'bass'].index(part)
            events.append((tick_on, mido.Message('note_on', note=pitch_to_midi(n['pitch']), velocity=vel, channel=ch)))
            events.append((tick_off, mido.Message('note_off', note=pitch_to_midi(n['pitch']), velocity=0, channel=ch)))

    # tempo events
    if mockup and not mechanical:
        for pt in mockup['tempo_map']:
            events.append((pt['division'] * TICKS_PER_DIV,
                           mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(pt['bpm']))))

    events.sort(key=lambda e: (e[0], 0 if e[1].type == 'set_tempo' else 1))
    track = mido.MidiTrack()
    mid.tracks.append(track)
    # program changes: choir aahs (52) on each channel
    for ch in range(4):
        track.append(mido.Message('program_change', program=52, channel=ch, time=0))
    last = 0
    for tick, msg in events:
        track.append(msg.copy(time=tick - last))
        last = tick
    mid.save(out_path)
    print('wrote', out_path, '| events:', len(events))

build('/tmp/chorale-phrase.json', None, '/tmp/chorale-mechanical.mid', mechanical=True)
build('/tmp/chorale-phrase.json', '/tmp/mockup-v1.json', '/tmp/chorale-mockup-v1.mid', mechanical=False)
