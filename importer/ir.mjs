// Importer intermediate representation (IR) — issue #16, per docs/scope-importer.md.
// The neutral structure both the MIDI (#17) and MusicXML (#18) parsers emit and
// synthesis (#19) consumes. Canonical time unit is beats (quarter notes); pitch
// is a MIDI note number (middle C = C4 = 60) with optional MusicXML spelling
// metadata. Nothing downstream of this module sees ticks or seconds.

const SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const STEP_SEMITONES = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

const checkMidi = (midi) => {
  if (!Number.isInteger(midi) || midi < 0 || midi > 127)
    throw new RangeError(`midi note number out of range: ${midi}`);
};

// Canonical emission uses sharps; the schema's pitch grammar is a plain string
// (e.g. material.motifs[].pitches, constraints.register bounds).
export const midiToPitch = (midi) => {
  checkMidi(midi);
  return `${SHARP_NAMES[midi % 12]}${Math.floor(midi / 12) - 1}`;
};

const PITCH_RE = /^([A-G])(#|b)?(-?\d+)$/;
export const pitchToMidi = (pitch) => {
  const m = PITCH_RE.exec(pitch);
  if (!m) throw new Error(`invalid pitch: ${pitch}`);
  const alter = m[2] === "#" ? 1 : m[2] === "b" ? -1 : 0;
  const midi = STEP_SEMITONES[m[1]] + alter + (Number(m[3]) + 1) * 12;
  checkMidi(midi);
  return midi;
};

// MusicXML step/alter/octave spelling. Integer alter only: a microtonal alter
// has no MIDI note number, so representing it is a parser-side lossy decision,
// not something to paper over here.
export const spellingToMidi = ({ step, alter = 0, octave }) => {
  if (!(step in STEP_SEMITONES)) throw new Error(`invalid spelling step: ${step}`);
  if (!Number.isInteger(alter))
    throw new Error(`microtonal alter not representable as MIDI note number: ${alter}`);
  if (!Number.isInteger(octave)) throw new Error(`invalid spelling octave: ${octave}`);
  const midi = STEP_SEMITONES[step] + alter + (octave + 1) * 12;
  checkMidi(midi);
  return midi;
};

export const midiToSpelling = (midi) => {
  checkMidi(midi);
  const name = SHARP_NAMES[midi % 12];
  return { step: name[0], alter: name.length > 1 ? 1 : 0, octave: Math.floor(midi / 12) - 1 };
};

// Parsers convert source ticks to beats at the IR boundary.
export const ticksToBeats = (ticks, ticksPerQuarter) => ticks / ticksPerQuarter;
export const beatsToTicks = (beats, ticksPerQuarter) => Math.round(beats * ticksPerQuarter);

// --- Validation ---
// validateIR returns human-readable errors (empty = valid), mirroring
// tools/semantics.mjs. Shape invariants only; content policy (e.g. "an import
// must have a tempo") belongs to synthesis.

const NOTE_KEYS = ["midi", "spelling", "onsetBeat", "durationBeats", "velocity"];
const PART_KEYS = ["id", "name", "program", "notes"];
const TOP_KEYS = ["tempoMap", "meterMap", "keyMap", "parts"];

const unknownKeys = (obj, allowed) => Object.keys(obj).filter((k) => !allowed.includes(k));
const isNonNeg = (n) => typeof n === "number" && Number.isFinite(n) && n >= 0;

const checkMap = (errors, doc, field, entryCheck) => {
  const map = doc[field];
  if (!Array.isArray(map)) {
    errors.push(`${field}: required, must be an array (empty allowed — e.g. unknown key)`);
    return;
  }
  map.forEach((entry, i) => {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
      errors.push(`${field}[${i}]: must be an object`);
      return;
    }
    if (!isNonNeg(entry.beat)) errors.push(`${field}[${i}].beat: must be a number >= 0`);
    entryCheck(entry, i);
  });
};

export function validateIR(doc) {
  const errors = [];
  if (!doc || typeof doc !== "object" || Array.isArray(doc)) return ["IR document must be an object"];
  for (const k of unknownKeys(doc, TOP_KEYS)) errors.push(`${k}: unknown top-level field`);

  checkMap(errors, doc, "tempoMap", (e, i) => {
    for (const k of unknownKeys(e, ["beat", "bpm"])) errors.push(`tempoMap[${i}].${k}: unknown field`);
    if (!(typeof e.bpm === "number" && e.bpm > 0)) errors.push(`tempoMap[${i}].bpm: must be a number > 0`);
  });

  checkMap(errors, doc, "meterMap", (e, i) => {
    for (const k of unknownKeys(e, ["beat", "beats", "unit"])) errors.push(`meterMap[${i}].${k}: unknown field`);
    const beatsOk =
      (Number.isInteger(e.beats) && e.beats >= 1) ||
      (Array.isArray(e.beats) && e.beats.length >= 2 && e.beats.every((b) => Number.isInteger(b) && b >= 1));
    if (!beatsOk) errors.push(`meterMap[${i}].beats: must be an integer >= 1 or an array of 2+ integers >= 1`);
    if (!(Number.isInteger(e.unit) && e.unit >= 1)) errors.push(`meterMap[${i}].unit: must be an integer >= 1`);
  });

  checkMap(errors, doc, "keyMap", (e, i) => {
    for (const k of unknownKeys(e, ["beat", "tonic", "mode"])) errors.push(`keyMap[${i}].${k}: unknown field`);
    if (!(typeof e.tonic === "string" && e.tonic.length > 0)) errors.push(`keyMap[${i}].tonic: required string`);
    // Mirrors globals.schema.json: mode required unless the key is atonal.
    if (e.tonic !== "atonal" && !(typeof e.mode === "string" && e.mode.length > 0))
      errors.push(`keyMap[${i}].mode: required unless tonic is "atonal"`);
  });

  if (!Array.isArray(doc.parts)) {
    errors.push("parts: required, must be an array");
    return errors;
  }
  const seenIds = new Set();
  doc.parts.forEach((part, pi) => {
    const at = `parts[${pi}]`;
    if (!part || typeof part !== "object" || Array.isArray(part)) {
      errors.push(`${at}: must be an object`);
      return;
    }
    for (const k of unknownKeys(part, PART_KEYS)) errors.push(`${at}.${k}: unknown field`);
    if (!(typeof part.id === "string" && part.id.length > 0)) errors.push(`${at}.id: required non-empty string`);
    else if (seenIds.has(part.id)) errors.push(`${at}.id: duplicate part id "${part.id}"`);
    else seenIds.add(part.id);
    if (!(typeof part.name === "string" && part.name.length > 0)) errors.push(`${at}.name: required non-empty string`);
    if (part.program !== undefined && !(Number.isInteger(part.program) && part.program >= 0 && part.program <= 127))
      errors.push(`${at}.program: must be an integer 0-127`);
    if (!Array.isArray(part.notes)) {
      errors.push(`${at}.notes: required, must be an array`);
      return;
    }
    part.notes.forEach((note, ni) => {
      const nat = `${at}.notes[${ni}]`;
      if (!note || typeof note !== "object" || Array.isArray(note)) {
        errors.push(`${nat}: must be an object`);
        return;
      }
      for (const k of unknownKeys(note, NOTE_KEYS)) errors.push(`${nat}.${k}: unknown field`);
      if (!(Number.isInteger(note.midi) && note.midi >= 0 && note.midi <= 127))
        errors.push(`${nat}.midi: must be an integer 0-127`);
      if (!isNonNeg(note.onsetBeat)) errors.push(`${nat}.onsetBeat: must be a number >= 0`);
      if (!(typeof note.durationBeats === "number" && note.durationBeats > 0))
        errors.push(`${nat}.durationBeats: must be a number > 0`);
      if (note.velocity !== undefined && !(Number.isInteger(note.velocity) && note.velocity >= 0 && note.velocity <= 127))
        errors.push(`${nat}.velocity: must be an integer 0-127`);
      if (note.spelling !== undefined) {
        try {
          // Spelling is metadata for the composer's preferred enharmonic; it
          // must agree with the midi number it annotates.
          if (spellingToMidi(note.spelling) !== note.midi)
            errors.push(`${nat}.spelling: does not match midi ${note.midi} (${midiToPitch(note.midi)})`);
        } catch (e) {
          errors.push(`${nat}.spelling: ${e.message}`);
        }
      }
    });
  });
  return errors;
}

// Canonical form: maps sorted by beat, notes sorted by (onsetBeat, midi),
// stable key order. Part order is score order and is preserved. Sorts are
// stable (ES2019+), so entries sharing a beat keep emission order.
export const normalizeIR = (doc) => {
  const byBeat = (a) => [...a].sort((x, y) => x.beat - y.beat);
  return {
    tempoMap: byBeat(doc.tempoMap ?? []),
    meterMap: byBeat(doc.meterMap ?? []),
    keyMap: byBeat(doc.keyMap ?? []),
    parts: (doc.parts ?? []).map((p) => {
      const part = { id: p.id, name: p.name };
      if (p.program !== undefined) part.program = p.program;
      part.notes = [...(p.notes ?? [])]
        .sort((a, b) => a.onsetBeat - b.onsetBeat || a.midi - b.midi)
        .map((n) => {
          const note = { midi: n.midi };
          if (n.spelling !== undefined) note.spelling = n.spelling;
          note.onsetBeat = n.onsetBeat;
          note.durationBeats = n.durationBeats;
          if (n.velocity !== undefined) note.velocity = n.velocity;
          return note;
        });
      return part;
    }),
  };
};
