// End-to-end demo (issue #25): .muse.json → expansion → performance doc → WAV.
// Single entry point, per docs/scope-batch3.md. Default expansion is the
// offline deterministic expander (no API key needed); set MUSE_PROVIDER +
// MUSE_MODEL + provider key to use a live LLM via interpreter/expand.mjs.
// Usage: node tools/play.mjs <doc.muse.json> [rendition-id] [--out dir]
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { expandOffline } from "../interpreter/offline.mjs";
import { renderWav } from "../player/render.mjs";

const [docPath, renditionId, ...rest] = process.argv.slice(2);
if (!docPath) {
  console.error("usage: node tools/play.mjs <doc.muse.json> [rendition-id] [--out dir]");
  process.exit(1);
}
const outIdx = rest.indexOf("--out");
const outDir = outIdx >= 0 ? rest[outIdx + 1] : "out";
const barsIdx = rest.indexOf("--bars");
const maxBars = barsIdx >= 0 ? Number(rest[barsIdx + 1]) : Infinity;

const doc = JSON.parse(await readFile(docPath, "utf8"));
// --bars N: demo excerpt — truncate the form order to N bars total.
if (Number.isFinite(maxBars)) {
  const kept = [];
  let bars = 0;
  for (const id of doc.form?.order ?? []) {
    if (bars >= maxBars) break;
    kept.push(id);
    bars += doc.form.sections.find((s) => s.id === id)?.bars ?? 4;
  }
  doc.form.order = kept;
}
const renditions = doc.renditions ?? [];
const rendition = renditionId
  ? renditions.find((r) => r.id === renditionId)
  : renditions.length === 1 ? renditions[0] : renditions.find((r) => r.id === "r.default") ?? renditions[0];
if (!rendition) {
  console.error(renditionId ? `rendition "${renditionId}" not found` : "no renditions in document");
  process.exit(1);
}

// Live-model path when configured; offline expander otherwise.
let perf;
if (process.env.MUSE_MODEL) {
  const { expand, defaultModelConfig } = await import("../interpreter/expand.mjs");
  const { callModel, model } = defaultModelConfig();
  ({ perf } = await expand({ doc, renditionId: rendition.id, callModel, model }));
} else {
  perf = expandOffline(doc, rendition);
}

await mkdir(outDir, { recursive: true });
const base = `${path.basename(docPath).replace(/\.muse\.json$/, "")}.${rendition.id}`;
const perfPath = path.join(outDir, `${base}.muse.perf.json`);
const wavPath = path.join(outDir, `${base}.wav`);
await writeFile(perfPath, JSON.stringify(perf, null, 2) + "\n");
await writeFile(wavPath, renderWav(perf));
const secs = perf.notes.reduce((m, n) => Math.max(m, n.onset + n.duration), 0).toFixed(1);
console.log(`${docPath} [${rendition.id} "${rendition.name ?? ""}"] → ${perf.notes.length} notes, ~${secs}s`);
console.log(`  perf: ${perfPath}`);
console.log(`  wav:  ${wavPath}`);
