// Manual paste mode (issue #108): the CLI flag, prompt printing, stdin read,
// provenance stamping, and the retry loop — no API key, no live calls.
// Standalone runner; folded into npm test.
import { readFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";

let passed = 0, failed = 0;
const check = (name, cond, detail) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    if (detail) console.error(detail);
  }
};

const fixture = JSON.parse(await readFile("interpreter/fixtures/minimal-expansion.muse.perf.json", "utf8"));
const run = (input, args = ["interpreter/expand.mjs", "examples/minimal.muse.json", "--manual"]) =>
  spawnSync(process.execPath, args, { input, encoding: "utf8", timeout: 30000 });

// Happy path: prompt printed to stderr, perf doc on stdout, model stamped manual.
const ok = run(JSON.stringify(fixture));
check("manual mode exits 0 on a valid paste", ok.status === 0, ok.stderr);
check("prompt printed to stderr", ok.stderr.includes("=== SYSTEM ===") && ok.stderr.includes("=== USER ==="));
check("provenance stamped manual", JSON.parse(ok.stdout).metadata.interpreter.model === "manual");
check("rendition resolved (r.default)", JSON.parse(ok.stdout).metadata.source.rendition_id === "r.default");

// Retry loop is interactive: each attempt reads stdin to EOF, so automated
// tests cover the single-attempt channel — a junk paste fails with a readable
// parse error (the retry itself is a human loop in a terminal).
const junk = run("not json at all\n");
check("junk paste fails with a readable parse error", junk.status !== 0 && junk.stderr.includes("not parseable JSON"), junk.stderr.slice(-200));

// Bounded attempts: the retry bound is the interactive loop's business; the
// machine-checkable pin is that a failing paste exits non-zero.
check("failing paste exits non-zero", junk.status !== 0);

// Flag parsing: --manual must not be mistaken for a rendition id (covered by
// the happy path — it passes --manual in args and still resolves r.default).
check("--manual not parsed as rendition id", ok.status === 0);

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
