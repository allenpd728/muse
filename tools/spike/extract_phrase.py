import zipfile, json
import xml.etree.ElementTree as ET

z = zipfile.ZipFile('/workspace/muse/corpus/bach/bwv227.1.mxl')
inner = [n for n in z.namelist() if n.endswith('.xml') and 'container' not in n][0]
root = ET.fromstring(z.read(inner))

parts_meta = {}
for sp in root.iter('score-part'):
    pid = sp.get('id')
    name = sp.find('part-name')
    parts_meta[pid] = name.text if name is not None else pid

result = {'divisions': None, 'parts': {}}
for part in root.iter('part'):
    pid = part.get('id')
    name = parts_meta.get(pid, pid).lower()
    notes = []
    cursor = 0
    divisions = None
    for meas in list(part)[:9]:
        for el in meas:
            if el.tag == 'attributes':
                d = el.find('divisions')
                if d is not None:
                    divisions = int(d.text)
            elif el.tag == 'note':
                dur_el = el.find('duration')
                dur = int(dur_el.text) if dur_el is not None else 0
                if el.find('rest') is not None:
                    cursor += dur
                    continue
                pitch_el = el.find('pitch')
                if pitch_el is None:
                    cursor += dur
                    continue
                step = pitch_el.find('step').text
                alter_el = pitch_el.find('alter')
                alter = int(alter_el.text) if alter_el is not None else 0
                octave = pitch_el.find('octave').text
                acc = '#' * alter if alter > 0 else 'b' * (-alter)
                is_chord = el.find('chord') is not None
                onset = notes[-1]['onset'] if is_chord and notes else cursor
                notes.append({'pitch': f'{step}{acc}{octave}', 'onset': onset, 'duration': dur})
                if not is_chord:
                    cursor += dur
    if divisions and result['divisions'] is None:
        result['divisions'] = divisions
    result['parts'][name] = notes
    print(name, len(notes), 'notes, ends at division', cursor)

json.dump(result, open('/tmp/chorale-phrase.json', 'w'), indent=1)
print('divisions per quarter:', result['divisions'])
