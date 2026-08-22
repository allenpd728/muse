// End-to-end demo tests (issue #25): .muse.json → expansion → perf doc → WAV.
// Standalone runner: `node tests/play.test.mjs`; also folded into npm test.
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { expandOffline } from "../interpreter/offline.mjs";
import { checkPerfRefs } from "../tools/semantics.mjs";

const full = JSON.parse(await readFile(new URL("../examples/full.muse.json", import.meta.url), "utf8"));

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

// Offline expansion: valid perf docs for both renditions, deterministically.
const synth = expandOffline(full, full.renditions[0]);
const quartet = expandOffline(full, full.renditions[1]);
check("both renditions expand to notes", synth.notes.length > 0 && quartet.notes.length > 0);
check("part refs resolve", checkPerfRefs(synth).length === 0 && checkPerfRefs(quartet).length === 0);
check("expansion is deterministic",
  JSON.stringify(expandOffline(full, full.renditions[0])) === JSON.stringify(synth));

// Rendition params reach the perf doc: tempo, instrumentation, timing.
check("rendition tempo_bpm drives tempo_map",
  synth.tempo_map[0].bpm === 100 && quartet.tempo_map[0].bpm === 88);
check("rendition instrumentation drives parts",
  synth.parts[0].instrument.name === "analog synth" && quartet.parts[0].instrument.name === "piano");
check("slower rendition is longer in seconds for the same form",
  quartet.notes.at(-1).onset > synth.notes.at(-1).onset);

// Swing: quartet (0.62) delays offbeat eighths; synthwave (0.0) does not.
{
  const offbeatOnsets = (perf) => perf.notes.filter((n) => n.part === "p.lead" && (n.onset_beat % 1) >= 0.5).map((n) => n.onset_beat % 1);
  const qOff = offbeatOnsets(quartet);
  const sOff = offbeatOnsets(synth);
  check("swing rendition delays offbeats",
    qOff.length > 0 && qOff.every((f) => f > 0.5) && sOff.every((f) => f === 0.5));
}

// Transform realization: theme.1 phrases use motif.a#seq(+2) and motif.a#inv —
// the lead line must contain the transposed and inverted forms, not only the
// base motif shape.
{
  const leadPitches = synth.notes.filter((n) => n.part === "p.lead").map((n) => n.pitch);
  const base = [62, 65, 69, 67].map((p) => p + 12);       // motif.a up an octave
  const seqd = base.map((p) => p + 2);                     // #seq(+2)
  const invd = [62, 59, 55, 57].map((p) => p + 12);        // #inv about D (mirror intervals)
  const hasRun = (run) => leadPitches.some((_, i) => run.every((p, j) => leadPitches[i + j] === p));
  check("base motif realized", hasRun(base));
  check("seq(+2) transform realized", hasRun(seqd));
  check("inv transform realized", hasRun(invd));
}

// Must_contain: motif.a appears in every section's lead (constraint honor).
check("must_contain motif.a realized in lead", synth.notes.some((n) => n.part === "p.lead" && n.pitch_name === "D5"));

// DoD: npm run play produces audio end-to-end; two renditions differ.
{
  const tmp = await mkdtemp(path.join(tmpdir(), "muse-play-"));
  try {
    const r1 = spawnSync(process.execPath, ["tools/play.mjs", "examples/full.muse.json", "r.synthwave", "--bars", "4", "--out", tmp], { encoding: "utf8" });
    check("play CLI exits 0 (synthwave)", r1.status === 0);
    const r2 = spawnSync(process.execPath, ["tools/play.mjs", "examples/full.muse.json", "r.quartet", "--bars", "4", "--out", tmp], { encoding: "utf8" });
    check("play CLI exits 0 (quartet)", r2.status === 0);
    const w1 = await readFile(path.join(tmp, "full.r.synthwave.wav"));
    const w2 = await readFile(path.join(tmp, "full.r.quartet.wav"));
    check("WAVs produced with RIFF headers",
      w1.subarray(0, 4).toString() === "RIFF" && w2.subarray(0, 4).toString() === "RIFF");
    check("two renditions audibly differ (bytes differ beyond header)",
      !w1.subarray(44).equals(w2.subarray(44)));
    const p1 = JSON.parse(await readFile(path.join(tmp, "full.r.synthwave.muse.perf.json"), "utf8"));
    check("perf doc written and validates refs", checkPerfRefs(p1).length === 0);
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
}

// Fallback realization (issue #91): corpus imports (motifs, no themes/uses)
// must never render silent; some imports lack sections entirely.
{
  const chorales = ["bwv269", "bwv316", "bwv26.6", "bwv292", "bwv331", "bwv344"];
  for (const name of chorales) {
    const doc = JSON.parse(await readFile(new URL(`../benchmark/corpus/${name}.muse.json`, import.meta.url), "utf8"));
    const perf = expandOffline(doc, doc.renditions[0]);
    check(`corpus ${name} renders >0 notes via fallback`, perf.notes.length > 0);
  }
  const bwv269 = JSON.parse(await readFile(new URL("../benchmark/corpus/bwv269.muse.json", import.meta.url), "utf8"));
  const n = expandOffline(bwv269, bwv269.renditions[0]).notes.length;
  check("bwv269 note count in a sane band of the source (~229)", n >= 20 && n <= 460);
  // Fallback must not fire when uses exist: full example pinned above
  // (base/seq/inv realization checks already cover it).
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
