#!/usr/bin/env node
// Import CLI (issue #20, per docs/scope-importer.md):
// `node importer/cli.mjs <file.mid|file.musicxml|file.mxl> -o out.muse.json`.
// Format detected by magic bytes first, extension as fallback; output is
// validated against schema/muse.schema.json before writing — the importer
// never emits a non-validating document.
import { readFile, writeFile } from "node:fs/promises";
import { basename } from "node:path";
import { fileURLToPath } from "node:url";
import { midiToIR } from "./midi.mjs";
import { parseMusicXML } from "./musicxml.mjs";
import { synthesize } from "./synthesize.mjs";

const [inputPath, ...rest] = process.argv.slice(2);
const outFlag = rest.indexOf("-o");
const outPath = outFlag >= 0 ? rest[outFlag + 1] : null;

if (!inputPath || !outPath) {
  console.error("usage: node importer/cli.mjs <file.mid|file.musicxml|file.mxl> -o out.muse.json");
  process.exit(1);
}

const bytes = await readFile(inputPath).catch((e) => {
  console.error(`error: cannot read ${inputPath}: ${e.code ?? e.message}`);
  process.exit(1);
});
const name = basename(inputPath);
const isMidi = bytes.length > 4 && bytes[0] === 0x4d && bytes[1] === 0x54 && bytes[2] === 0x68 && bytes[3] === 0x64;
const isZip = bytes.length > 4 && bytes[0] === 0x50 && bytes[1] === 0x4b;
const format = isMidi ? "midi" : isZip || /\.(musicxml|xml)$/i.test(name) ? "musicxml" : null;
if (!format) {
  console.error(`error: cannot detect format of ${name} (expected MIDI or MusicXML magic bytes / extension)`);
  process.exit(1);
}

const ir = format === "midi" ? midiToIR(bytes) : parseMusicXML(bytes, { filename: name });
const doc = synthesize(ir, { title: name.replace(/\.(mid|midi|musicxml|xml|mxl)$/i, ""), source: `${name} (${format})` });

// Validate before writing (scope doc hard rule).
const { spawnSync } = await import("node:child_process");
const tmp = `${outPath}.tmp-${process.pid}.json`;
await writeFile(tmp, JSON.stringify(doc, null, 2)).catch((e) => {
  console.error(`error: cannot write to ${outPath}: ${e.code ?? e.message}`);
  process.exit(1);
});
const check = spawnSync(process.execPath, [fileURLToPath(new URL("../tools/validate.mjs", import.meta.url)), tmp], { encoding: "utf8" });
if (check.status !== 0) {
  console.error(`error: synthesized document failed validation:\n${check.stderr}`);
  const { rm } = await import("node:fs/promises");
  await rm(tmp, { force: true }); // never emit a non-validating document
  process.exit(1);
}
const { rename } = await import("node:fs/promises");
await rename(tmp, outPath);
console.log(`imported: ${name} → ${outPath}`);
console.log(`  format: ${format} | parts: ${ir.parts.length} | motifs: ${doc.material?.motifs?.length ?? 0} | inferred: ${doc.extensions?.importer?.inferred?.length ?? 0}`);
