// Player V1 CLI + WAV wrapper (issue #24, per docs/scope-batch3.md).
// The pure renderer (render, droppedTechniques) lives in render-core.mjs —
// browser-safe for the listener (#97/#98). This file adds the node-only
// pieces: 16-bit PCM WAV encoding (Buffer) and the CLI.
import { render, encodeWav } from "./render-core.mjs";
export { render, droppedTechniques, encodeWav } from "./render-core.mjs";

export function renderWav(perfDoc, { sampleRate = 44100 } = {}) {
  return Buffer.from(encodeWav(render(perfDoc, { sampleRate }), { sampleRate }));
}

// --- CLI ---
import path from "node:path";
const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === new URL(import.meta.url).pathname;
if (invokedDirectly) {
  const { readFile, writeFile } = await import("node:fs/promises");
  const [perfPath, outPath] = process.argv.slice(2);
  if (!perfPath || !outPath) {
    console.error("usage: node player/render.mjs <doc.muse.perf.json> <out.wav>");
    process.exit(1);
  }
  const perf = JSON.parse(await readFile(perfPath, "utf8"));
  await writeFile(outPath, renderWav(perf));
  const secs = (perf.notes ?? []).reduce((m, n) => Math.max(m, n.onset + n.duration), 0).toFixed(2);
  console.error(`rendered ${perfPath} → ${outPath} (${(perf.notes ?? []).length} notes, ~${secs}s)`);
}
