// Tests for importer/musicxml.mjs — issue #18 (Batch 2: MusicXML parser → IR).
// Standalone runner: `node tests/musicxml.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import { parseMusicXML } from "../importer/musicxml.mjs";

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// Public-domain chorale fixture: J.S. Bach BWV 269, from the music21 corpus
// (music21/corpus/bach/bwv269.mxl). Compressed `.mxl` exercises fflate +
// META-INF/container.xml rootfile resolution.
const choraleBytes = await readFile(new URL("../importer/fixtures/bwv269.mxl", import.meta.url));
const chorale = parseMusicXML(choraleBytes, { filename: "not-a-mxl-name.bin" });
check("chorale .mxl parses with 4 SATB parts", chorale.parts.length === 4);
check("part names come from score-part part-list", eq(chorale.parts.map((p) => p.name), ["Soprano", "Alto", "Tenor", "Bass"]));
check("opening key is G major from fifths=1/mode=major", eq(chorale.keyMap, [{ beat: 0, tonic: "G", mode: "major" }]));
check("opening meter is 3/4", eq(chorale.meterMap, [{ beat: 0, beats: 3, unit: 4 }]));
check("no tempo direction means empty tempoMap (not invented)", eq(chorale.tempoMap, []));
check("soprano opening is notated G4 quarter pickup", eq(chorale.parts[0].notes[0], {
  midi: 67,
  spelling: { step: "G", alter: 0, octave: 4 },
  onsetBeat: 0,
  durationBeats: 1,
}));
check("divisions convert to beats (dotted quarter = 1.5)", eq(chorale.parts[0].notes[3], {
  midi: 71,
  spelling: { step: "B", alter: 0, octave: 4 },
  onsetBeat: 4,
  durationBeats: 1.5,
}));
check("key signature accidentals reach spelling (bass F#3)", chorale.parts[3].notes.some((n) =>
  n.onsetBeat === 3 && n.midi === 54 && n.spelling?.step === "F" && n.spelling?.alter === 1));
check("chorale note total is stable (229 IR notes)", chorale.parts.reduce((sum, p) => sum + p.notes.length, 0) === 229);

// Uncompressed score-partwise input + tempo direction + chord/backup handling.
const tiny = `<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>Piano</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>2</divisions><key><fifths>0</fifths><mode>major</mode></key><time><beats>4</beats><beat-type>4</beat-type></time></attributes>
      <direction><sound tempo="84"/></direction>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration></note>
      <note><chord/><pitch><step>E</step><octave>4</octave></pitch><duration>2</duration></note>
      <backup><duration>2</duration></backup>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>2</duration></note>
    </measure>
  </part>
</score-partwise>`;
const tinyIr = parseMusicXML(tiny, { filename: "tiny.musicxml" });
check("uncompressed score-partwise string parses", tinyIr.parts.length === 1);
check("sound tempo becomes tempoMap", eq(tinyIr.tempoMap, [{ beat: 0, bpm: 84 }]));
check("chord tone shares onset with previous note", eq(tinyIr.parts[0].notes.filter((n) => n.onsetBeat === 0 && [60, 64].includes(n.midi)).map((n) => [n.midi, n.onsetBeat, n.durationBeats]), [[60, 0, 1], [64, 0, 1]]));
check("backup rewinds cursor for lower voice", eq(tinyIr.parts[0].notes.find((n) => n.midi === 55), {
  midi: 55,
  spelling: { step: "G", alter: 0, octave: 3 },
  onsetBeat: 0,
  durationBeats: 1,
}));
check("parser rejects timewise root for now", (() => {
  try { parseMusicXML("<score-timewise version=\"4.0\"/>", { filename: "x.musicxml" }); return false; } catch { return true; }
})());

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
