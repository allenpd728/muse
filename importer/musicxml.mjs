// MusicXML → importer IR (issue #18), per docs/scope-importer.md.
// Uses musicxml-interfaces' element parsers over a partwise DOM directly rather
// than parseScore(): parseScore() shells out to xsltproc, and the importer must
// stay pure-JS for CI. `.mxl` containers are opened with fflate.
import { DOMParser, XMLSerializer } from "@xmldom/xmldom";
import { unzipSync } from "fflate";
import {
  paseScoreHeader,
  parseAttributes,
  parseBackup,
  parseDirection,
  parseForward,
  parseNote,
} from "musicxml-interfaces";
import { normalizeIR, spellingToMidi, validateIR } from "./ir.mjs";

const elementProto = new DOMParser().parseFromString("<_ />", "text/xml").documentElement.constructor.prototype;
if (!Object.getOwnPropertyDescriptor(elementProto, "children")) {
  Object.defineProperty(elementProto, "children", {
    get() {
      return Array.from(this.childNodes ?? []).filter((n) => n.nodeType === 1);
    },
    configurable: true,
  });
}

const MAJOR_BY_FIFTHS = ["Cb", "Gb", "Db", "Ab", "Eb", "Bb", "F", "C", "G", "D", "A", "E", "B", "F#", "C#"];
const LETTERS = ["C", "D", "E", "F", "G", "A", "B"];
const NATURAL_PC = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
const MODE_STEP = { ionian: 0, major: 0, dorian: 1, phrygian: 2, lydian: 3, mixolydian: 4, aeolian: 5, minor: 5, locrian: 6 };
const MODE_OFFSET = { ionian: 0, major: 0, dorian: 2, phrygian: 4, lydian: 5, mixolydian: 7, aeolian: 9, minor: 9, locrian: 11 };

const spellingName = ({ step, alter = 0 }) => `${step}${alter > 0 ? "#".repeat(alter) : alter < 0 ? "b".repeat(-alter) : ""}`;

const keyFromSignature = ({ fifths, mode }) => {
  if (!Number.isInteger(fifths) || fifths < -7 || fifths > 7) return null;
  const modeName = String(mode || "major").toLowerCase();
  if (modeName === "none") return { tonic: "atonal" };
  if (!(modeName in MODE_OFFSET)) return null;
  const major = MAJOR_BY_FIFTHS[fifths + 7];
  const stepIndex = (LETTERS.indexOf(major[0]) + MODE_STEP[modeName]) % 7;
  const step = LETTERS[stepIndex];
  const targetPc = (NATURAL_PC[major[0]] + (major[1] === "#" ? 1 : major[1] === "b" ? -1 : 0) + MODE_OFFSET[modeName] + 120) % 12;
  const alter = targetPc - NATURAL_PC[step];
  return { tonic: spellingName({ step, alter }), mode: modeName === "minor" ? "minor" : modeName };
};

const meterFromTime = (time) => {
  const units = time.beatTypes ?? [];
  const unit = units[0];
  if (!Number.isInteger(unit) || unit < 1 || units.some((u) => u !== unit)) return null;
  const rawBeats = (time.beats ?? []).flatMap((b) => String(b).split("+")).map((b) => Number.parseInt(b, 10));
  if (rawBeats.length === 0 || rawBeats.some((b) => !Number.isInteger(b) || b < 1)) return null;
  return { beats: rawBeats.length === 1 ? rawBeats[0] : rawBeats, unit };
};

const tempoFromDirection = (direction) => {
  const soundTempo = Number.parseFloat(direction?.sound?.tempo ?? "");
  if (Number.isFinite(soundTempo) && soundTempo > 0) return soundTempo;
  for (const type of direction?.directionTypes ?? []) {
    const bpm = Number.parseFloat(type?.metronome?.perMinute?.data ?? "");
    if (Number.isFinite(bpm) && bpm > 0) return bpm;
  }
  return null;
};

const bytesOf = (input) => {
  if (input instanceof Uint8Array) return input;
  if (Buffer.isBuffer(input)) return new Uint8Array(input.buffer, input.byteOffset, input.byteLength);
  return new TextEncoder().encode(String(input));
};

const isZip = (bytes) => bytes.length > 4 && bytes[0] === 0x50 && bytes[1] === 0x4b && bytes[2] === 0x03 && bytes[3] === 0x04;

const extractXml = (input, filename = "") => {
  const bytes = bytesOf(input);
  if (!isZip(bytes) && !/\.mxl$/i.test(filename)) return new TextDecoder().decode(bytes);
  const files = unzipSync(bytes);
  const decoder = new TextDecoder();
  const container = files["META-INF/container.xml"] ? decoder.decode(files["META-INF/container.xml"]) : "";
  const rootPath = /full-path="([^"]+)"/.exec(container)?.[1];
  if (rootPath && files[rootPath]) return decoder.decode(files[rootPath]);
  const fallback = Object.keys(files).find((name) => /\.(musicxml|xml)$/i.test(name));
  if (fallback) return decoder.decode(files[fallback]);
  throw new Error("mxl container has no MusicXML rootfile");
};

const addUnique = (map, entry, key) => {
  if (!map.some((existing) => key(existing) === key(entry))) map.push(entry);
};

const roundBeats = (n) => Math.round(n * 1e6) / 1e6;

export function parseMusicXML(input, { filename = "" } = {}) {
  const xml = extractXml(input, filename);
  const dom = new DOMParser().parseFromString(xml, "text/xml");
  const root = dom.documentElement;
  if (!root || root.nodeName !== "score-partwise")
    throw new Error("MusicXML parser expects a score-partwise document");

  const header = paseScoreHeader(xml);
  const partMeta = new Map();
  for (const item of header.partList ?? []) {
    if (item?._class !== "ScorePart" && !item?.partName) continue;
    const midiProgram = item?.midiInstruments?.[0]?.midiProgram;
    partMeta.set(item.id, {
      name: item?.partName?.partName || item.id,
      program: Number.isInteger(midiProgram) ? midiProgram - 1 : undefined,
    });
  }

  const serializer = new XMLSerializer();
  const tempoMap = [];
  const meterMap = [];
  const keyMap = [];
  const parts = [];

  for (const partEl of Array.from(root.getElementsByTagName("part"))) {
    const id = partEl.getAttribute("id");
    if (!id) continue;
    let divisions = 1;
    let cursor = 0;
    let lastOnset = 0;
    const notes = [];

    for (const measureEl of Array.from(partEl.children).filter((el) => el.nodeName === "measure")) {
      const measureStart = cursor;
      let measureEnd = cursor;
      for (const child of Array.from(measureEl.children)) {
        const childXml = serializer.serializeToString(child);
        if (child.nodeName === "attributes") {
          const attrs = parseAttributes(childXml);
          if (Number.isFinite(attrs.divisions) && attrs.divisions > 0) divisions = attrs.divisions;
          for (const key of attrs.keySignatures ?? []) {
            const parsedKey = keyFromSignature(key);
            if (parsedKey) addUnique(keyMap, { beat: roundBeats(cursor), ...parsedKey }, (e) => `${e.beat}|${e.tonic}|${e.mode ?? ""}`);
          }
          for (const time of attrs.times ?? []) {
            const meter = meterFromTime(time);
            if (meter) addUnique(meterMap, { beat: roundBeats(cursor), ...meter }, (e) => `${e.beat}|${JSON.stringify(e.beats)}|${e.unit}`);
          }
        } else if (child.nodeName === "direction") {
          const bpm = tempoFromDirection(parseDirection(childXml));
          if (bpm) addUnique(tempoMap, { beat: roundBeats(cursor), bpm }, (e) => `${e.beat}|${e.bpm}`);
        } else if (child.nodeName === "backup") {
          const duration = parseBackup(childXml).duration;
          if (Number.isFinite(duration)) cursor = Math.max(measureStart, cursor - duration / divisions);
        } else if (child.nodeName === "forward") {
          const duration = parseForward(childXml).duration;
          if (Number.isFinite(duration)) {
            cursor += duration / divisions;
            measureEnd = Math.max(measureEnd, cursor);
            lastOnset = cursor;
          }
        } else if (child.nodeName === "note") {
          const note = parseNote(childXml);
          if (note.grace || !Number.isFinite(note.duration)) continue;
          const durationBeats = note.duration / divisions;
          const isChord = !!note.chord;
          const onset = isChord ? lastOnset : cursor;
          if (!note.rest && note.pitch) {
            const spelling = {
              step: String(note.pitch.step).toUpperCase(),
              alter: Number.isInteger(note.pitch.alter) ? note.pitch.alter : 0,
              octave: note.pitch.octave,
            };
            notes.push({
              midi: spellingToMidi(spelling),
              spelling,
              onsetBeat: roundBeats(onset),
              durationBeats: roundBeats(durationBeats),
            });
          }
          if (isChord) measureEnd = Math.max(measureEnd, onset + durationBeats);
          else {
            cursor += durationBeats;
            measureEnd = Math.max(measureEnd, cursor);
            lastOnset = onset;
          }
        }
      }
      cursor = measureEnd;
    }

    const meta = partMeta.get(id) ?? { name: id };
    const part = { id, name: meta.name, notes };
    if (meta.program !== undefined) part.program = meta.program;
    parts.push(part);
  }

  const ir = normalizeIR({ tempoMap, meterMap, keyMap, parts });
  const errors = validateIR(ir);
  if (errors.length > 0) throw new Error(`MusicXML produced invalid IR:\n${errors.join("\n")}`);
  return ir;
}
