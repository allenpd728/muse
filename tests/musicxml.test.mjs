// Tests for importer/musicxml.mjs — issue #18 (Batch 2: MusicXML parser → IR).
// Standalone runner: `node tests/musicxml.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import { parseMusicXML } from "../importer/musicxml.mjs";
import { validateIR, normalizeIR } from "../importer/ir.mjs";

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

// --- Residual pins (issue #56, spec: tests/open_20260822-110500_musicxml-parser.md) ---

// Parser boundary conformance (per #16 spec): the chorale's IR validates and
// normalization is idempotent.
check("chorale IR passes validateIR", eq(validateIR(chorale), []));
check("normalizeIR is idempotent on parser output", eq(normalizeIR(normalizeIR(chorale)), normalizeIR(chorale)));

// Non-traditional key signatures (key-step/key-alter lists) and composite
// time signatures with mixed beat-types produce no IR entry and no crash.
const nonTraditional = `<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>Flute</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key><key-step>B</key-step><key-alter>-1</key-alter><key-step>E</key-step><key-alter>-1</key-alter></key>
        <time><beats>3</beats><beat-type>4</beat-type><beats>2</beats><beat-type>8</beat-type></time>
      </attributes>
      <note><pitch><step>D</step><octave>5</octave></pitch><duration>4</duration></note>
    </measure>
  </part>
</score-partwise>`;
const ntIr = parseMusicXML(nonTraditional, { filename: "nt.musicxml" });
check("non-traditional key signature: no keyMap entry, no crash", ntIr.keyMap.length === 0);
check("composite time with mixed beat-types: no meterMap entry, no crash", ntIr.meterMap.length === 0);
check("notes still parse when key/time are skipped", ntIr.parts[0].notes.length === 1 && ntIr.parts[0].notes[0].midi === 74);

// Mode mapping across the circle of fifths × modes. `fifths` is the key
// *signature's* fifths (standard MusicXML semantics): fifths=1 is one sharp
// (G major signature), and modes shift the tonic within that signature —
// dorian a step up, lydian a fourth up, minor down a third, etc.
const keyDoc = (fifths, mode) => `<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>X</part-name></score-part></part-list>
  <part id="P1"><measure number="1">
    <attributes><divisions>1</divisions><key><fifths>${fifths}</fifths><mode>${mode}</mode></key><time><beats>4</beats><beat-type>4</beat-type></time></attributes>
  </measure></part>
</score-partwise>`;
const tonicOf = (fifths, mode) => parseMusicXML(keyDoc(fifths, mode), { filename: "k.musicxml" }).keyMap[0];
check("mode map: 0 fifths minor is A minor", eq(tonicOf(0, "minor"), { beat: 0, tonic: "A", mode: "minor" }));
check("mode map: 1 fifth dorian is A dorian (G-major signature)", eq(tonicOf(1, "dorian"), { beat: 0, tonic: "A", mode: "dorian" }));
check("mode map: 2 fifths mixolydian is A mixolydian (D-major signature)", eq(tonicOf(2, "mixolydian"), { beat: 0, tonic: "A", mode: "mixolydian" }));
check("mode map: -2 fifths major is Bb major", eq(tonicOf(-2, "major"), { beat: 0, tonic: "Bb", mode: "major" }));
check("mode map: -1 fifth minor is D minor", eq(tonicOf(-1, "minor"), { beat: 0, tonic: "D", mode: "minor" }));
check("mode map: 3 fifths lydian is D lydian (A-major signature)", eq(tonicOf(3, "lydian"), { beat: 0, tonic: "D", mode: "lydian" }));

// Measure-boundary beats: <forward> across a measure line lands the next
// note at the right absolute beat.
const crossMeasure = `<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>X</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>0</fifths><mode>major</mode></key><time><beats>4</beats><beat-type>4</beat-type></time></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration></note>
      <forward><duration>2</duration></forward>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration></note>
    </measure>
    <measure number="2">
      <forward><duration>3</duration></forward>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>1</duration></note>
    </measure>
  </part>
</score-partwise>`;
const cmIr = parseMusicXML(crossMeasure, { filename: "cm.musicxml" });
check("forward carries across the measure boundary (E4 lands at beat 7)",
  eq(cmIr.parts[0].notes.map((n) => [n.midi, n.onsetBeat]), [[60, 0], [62, 3], [64, 7]]));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
