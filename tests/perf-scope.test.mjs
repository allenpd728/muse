// Consistency guards for the Batch 3 performance-layer scope (issue #61, per
// tests/open_20260822-121502_perf-layer-scope.md). The source task shipped
// documents, not code — these guards pin the formats those documents declare
// against each other and against existing grammars, so doc drift goes red.
// Standalone runner: `node tests/perf-scope.test.mjs`; folded into npm test.
import { readFileSync } from "node:fs";

let passed = 0, failed = 0;
const check = (name, cond, detail) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}${detail ? ` — ${detail}` : ""}`); }
};

const spec = readFileSync("SCHEMA_SPEC.md", "utf8");
const scopeDoc = readFileSync("docs/scope-batch3.md", "utf8");

// Extract the §7 jsonc example: the first ```jsonc block inside §7.
const section7 = spec.slice(spec.indexOf("## 7. Performance layer"));
const block = section7.match(/```jsonc\n([\s\S]*?)```/);
check("§7 contains a jsonc example", !!block);

// Strip // comments and trailing commas to get parseable JSON.
const jsonish = (block?.[1] ?? "")
  .replace(/\/\/[^\n"]*/g, "")
  .replace(/,\s*([}\]])/g, "$1");
const perf = JSON.parse(jsonish); // throws if unparseable — test run fails, which is the point
check("§7 example parses after comment/trailing-comma stripping", typeof perf === "object");

// Required top-level shape per §7/scope doc.
for (const key of ["muse_perf_version", "metadata", "tempo_map", "parts", "notes"])
  check(`§7 example has ${key}`, perf[key] !== undefined);
check("§7 metadata carries source + interpreter", perf.metadata?.source !== undefined && perf.metadata?.interpreter !== undefined);

// Both clocks on every note: seconds (onset/duration) + beats (onset_beat/duration_beats).
check("§7 notes carry both clocks", (perf.notes ?? []).every((n) =>
  n.onset !== undefined && n.duration !== undefined
  && n.onset_beat !== undefined && n.duration_beats !== undefined));

// pitch_name reuses the §2.3 pitch grammar pinned in the schemas (#44).
const materialSchema = JSON.parse(readFileSync("schema/material.schema.json", "utf8"));
const pitchPattern = materialSchema?.$defs?.pitch?.pattern ?? materialSchema?.properties?.motifs?.items?.properties?.pitches?.items?.pattern;
check("pitch grammar found in material schema", typeof pitchPattern === "string", "expected a pattern under $defs.pitch or motifs items");
if (pitchPattern) {
  const re = new RegExp(pitchPattern);
  check("§7 pitch_name values match the §2.3 grammar", (perf.notes ?? []).every((n) => re.test(n.pitch_name)),
    (perf.notes ?? []).map((n) => n.pitch_name).join(","));
}

// *.muse.perf.json must not match the harness's *.muse.json example glob —
// a rename can't silently pull perf docs into the schema-example loops.
const harnessGlob = (f) => f.endsWith(".muse.json"); // mirrors tools/test.mjs listJson
check("perf suffix does not collide with harness example glob", !harnessGlob("examples/invalid/x.muse.perf.json"));

// Renderer contract documented in the scope doc (grep-level guard; #22/#24
// supersede with real schemas/tests as they land).
check("scope doc declares capabilities signature", /capabilities\s*:\s*\(\s*\)/.test(scopeDoc));
check("scope doc declares render signature", /render\s*:\s*async\s*\(/.test(scopeDoc));

// Versioning discipline: muse_perf_version matches the same semver pattern
// as muse_version in the root schema — one regex source, reused.
const rootSchema = JSON.parse(readFileSync("schema/muse.schema.json", "utf8"));
const semverRe = new RegExp(rootSchema.properties.muse_version.pattern);
check("§7 muse_perf_version matches the muse_version semver pattern", semverRe.test(perf.muse_perf_version),
  perf.muse_perf_version);

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
