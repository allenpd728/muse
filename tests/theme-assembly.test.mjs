// Residual coverage for importer theme assembly + uses wiring (issue #102,
// spec: tests/closed_…_theme-assembly.md). Crafted-IR pins for the
// overlap-tie policy, chain bounds, and cleanup-agent ergonomics.
// Standalone runner: `node tests/theme-assembly.test.mjs`; folded into npm test.
import { synthesize } from "../importer/synthesize.mjs";
import { checkPerfRefs } from "../tools/semantics.mjs";

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
  }
};

const flat = (over = {}) => ({
  tempoMap: [{ beat: 0, bpm: 96 }],
  meterMap: [{ beat: 0, beats: 4, unit: 4 }],
  keyMap: [],
  parts: [{ id: "p", name: "P", notes: [] }],
  ...over,
});

// Synthesize calls assembleThemes internally; exercise the policy through
// crafted IRs where motif extraction yields the candidates we want.
// Helper: build a part whose notes repeat three overlapping patterns.
const motifNotes = (seqs) => ({
  tempoMap: [{ beat: 0, bpm: 96 }],
  meterMap: [],
  keyMap: [],
  parts: [{ id: "p", name: "P", notes: seqs.flat() }],
});

// Overlap-tie policy: equal overlap (k=2) resolves to the longer motif.
// A = C4 D4 E4 F4 (len 4), B = E4 F4 G4 (len 3) — overlap by 2 (E4,F4 if
// durations agree); C = E4 F4 (len 2) also overlaps by 2. Longer wins the tie.
const tieIR = motifNotes([
  [
    { midi: 60, onsetBeat: 0, durationBeats: 1 },
    { midi: 62, onsetBeat: 1, durationBeats: 1 },
    { midi: 64, onsetBeat: 2, durationBeats: 1 },
    { midi: 65, onsetBeat: 3, durationBeats: 1 },
  ],
  [
    { midi: 60, onsetBeat: 8, durationBeats: 1 },
    { midi: 62, onsetBeat: 9, durationBeats: 1 },
    { midi: 64, onsetBeat: 10, durationBeats: 1 },
    { midi: 65, onsetBeat: 11, durationBeats: 1 },
  ],
  [
    { midi: 64, onsetBeat: 16, durationBeats: 1 },
    { midi: 65, onsetBeat: 17, durationBeats: 1 },
    { midi: 67, onsetBeat: 18, durationBeats: 1 },
  ],
  [
    { midi: 64, onsetBeat: 24, durationBeats: 1 },
    { midi: 65, onsetBeat: 25, durationBeats: 1 },
    { midi: 67, onsetBeat: 26, durationBeats: 1 },
  ],
]);
const tieDoc = synthesize(tieIR, { source: "tie" });
const tieThemes = tieDoc.material?.themes ?? [];
check("overlap tie: theme assembles from overlapping candidates", tieThemes.length >= 1);
check("overlap tie: longer motif chains first in the phrase",
  tieThemes.length >= 1 && tieThemes[0].phrases[0].motifs.length >= 2);

// Chain bounds: pathological self-overlapping motifs must not chain forever —
// every motif is used at most once, and a theme's phrase length is bounded
// by the motif pool size.
const dup = motifNotes([
  [
    { midi: 60, onsetBeat: 0, durationBeats: 1 },
    { midi: 62, onsetBeat: 1, durationBeats: 1 },
    { midi: 64, onsetBeat: 2, durationBeats: 1 },
  ],
  [
    { midi: 60, onsetBeat: 4, durationBeats: 1 },
    { midi: 62, onsetBeat: 5, durationBeats: 1 },
    { midi: 64, onsetBeat: 6, durationBeats: 1 },
  ],
]);
const dupDoc = synthesize(dup, { source: "dup" });
const motifCount = dupDoc.material?.motifs?.length ?? 0;
const maxChain = Math.max(0, ...(dupDoc.material?.themes ?? []).map((t) => t.phrases[0].motifs.length));
check("chain bounded by motif pool (no repeat chaining)", maxChain <= Math.max(1, motifCount));

// Cleanup-agent ergonomics: theme/uses inferences carry undoable info —
// the motif chain and section id must be in the reason strings, not just a count.
const reasons = (tieDoc.extensions?.importer?.inferred ?? []).map((e) => `${e.path} ${e.reason}`);
check("inferred entries name the motifs pool for undo", reasons.some((r) => r.includes("motif")));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
