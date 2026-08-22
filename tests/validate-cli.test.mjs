// Tests for tools/validate.mjs (issue #26, spec: tests/open_20260821-233000_validator-cli.md).
// Standalone runner: `node tests/validate-cli.test.mjs`. Folds into the #3 harness when it lands.
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdtemp, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const run = promisify(execFile);
const CLI = new URL("../tools/validate.mjs", import.meta.url).pathname;

let passed = 0, failed = 0;
const ok = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

async function cli(args) {
  try {
    const { stdout, stderr } = await run("node", [CLI, ...args]);
    return { code: 0, stdout, stderr };
  } catch (e) {
    return { code: e.code ?? 1, stdout: e.stdout ?? "", stderr: e.stderr ?? "" };
  }
}

const dir = await mkdtemp(path.join(tmpdir(), "muse-validate-"));
const schema = path.join(dir, "schema.json");
await writeFile(schema, JSON.stringify({
  $schema: "https://json-schema.org/draft/2020-12/schema",
  type: "object",
  required: ["muse_version"],
  properties: { muse_version: { type: "string" } },
}));

const write = (name, content) => { const p = path.join(dir, name); return writeFile(p, content).then(() => p); };

const valid = await write("ok.json", JSON.stringify({ muse_version: "0.1" }));
const missingReq = await write("bad.json", "{}");
const wrongType = await write("badtype.json", JSON.stringify({ muse_version: 5 }));
const notJson = await write("notjson.json", "this is not json");
const empty = await write("empty.json", "{}");
const extra = await write("extra.json", JSON.stringify({ muse_version: "0.1", unknown: true }));
const badSchema = await write("badschema.json", "{ not valid json");

let r = await cli([valid, schema]);
ok("valid document exits 0 and prints valid:", r.code === 0 && /valid:/.test(r.stdout));

r = await cli([missingReq, schema]);
ok("missing required property exits 1 with ajv path", r.code === 1 && /invalid:/.test(r.stderr) && /muse_version/.test(r.stderr));

r = await cli([wrongType, schema]);
ok("wrong type exits 1 with readable error", r.code === 1 && /must be string/.test(r.stderr));

r = await cli([notJson, schema]);
ok("non-JSON document exits 1 without stack trace", r.code === 1 && /error:/.test(r.stderr) && !/at .*validate\.mjs/.test(r.stderr));

r = await cli([path.join(dir, "does-not-exist.json"), schema]);
ok("missing document file exits 1 with error message", r.code === 1 && /error:/.test(r.stderr));

r = await cli([valid, badSchema]);
ok("malformed schema exits 1 with schema error", r.code === 1 && /error:/.test(r.stderr));

r = await cli([]);
ok("no document argument exits 1 with usage", r.code === 1 && /usage:/.test(r.stderr));

r = await cli([empty, schema]);
ok("empty object against required schema exits 1", r.code === 1);

r = await cli([extra, schema]);
ok("unknown properties allowed when schema omits additionalProperties:false", r.code === 0);

// default schema path: run from repo root with only the document arg. The real
// root requires muse_version/metadata/globals and resolves relative $refs to
// pre-registered section siblings.
const rootValid = await write("root-ok.json", JSON.stringify({
  muse_version: "0.1.0",
  metadata: {
    id: "01J00000000000000000000000",
    title: "default path check",
    composer: { name: "harness" },
    created: "2026-08-22T00:00:00Z",
    license: { renditions: "presets-only", attribution: "required", commercial: true },
    provenance: []
  },
  globals: { tempo: { bpm: 96 } }
}));
r = await cli([rootValid]);
ok("default schema resolves $refs and validates composed doc", r.code === 0 && /valid:/.test(r.stdout));

await rm(dir, { recursive: true, force: true });

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
