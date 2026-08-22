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

// --- Residual coverage (issue #111) ---

// MUSE_MANUAL=1 takes the same path as the flag.
{
  const envRun = spawnSync(process.execPath, ["interpreter/expand.mjs", "examples/minimal.muse.json"], {
    input: JSON.stringify(fixture),
    encoding: "utf8",
    timeout: 30000,
    env: { ...process.env, MUSE_MANUAL: "1" },
  });
  check("MUSE_MANUAL=1 takes the manual path", envRun.status === 0
    && JSON.parse(envRun.stdout).metadata.interpreter.model === "manual", envRun.stderr.slice(-200));
}

// tools/play.mjs manual wiring: --manual routes through manualCall.
{
  const { mkdtempSync, rmSync, existsSync } = await import("node:fs");
  const { tmpdir } = await import("node:os");
  const path = await import("node:path");
  const tmp = mkdtempSync(path.join(tmpdir(), "muse-manual-play-"));
  try {
    const r = spawnSync(process.execPath, ["tools/play.mjs", "examples/minimal.muse.json", "--manual", "--out", tmp], {
      input: JSON.stringify(fixture),
      encoding: "utf8",
      timeout: 30000,
    });
    check("play --manual exits 0 and produces WAV", r.status === 0 && existsSync(path.join(tmp, "minimal.r.default.wav")), r.stderr.slice(-300));
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

// Retry feedback visible to the human: a junk first paste makes the second
// prompt carry the validation error text.
{
  // manualCall reads stdin to EOF per attempt; two pastes = two EOFs is not
  // expressible in one stdin stream, so the machine-checkable pin is the
  // expand-level loop: a scripted callModel that fails once, then succeeds,
  // with feedback asserted on the second prompt — the same loop manualCall
  // feeds.
  const { expand } = await import("../interpreter/expand.mjs");
  const minimal = JSON.parse(await readFile("examples/minimal.muse.json", "utf8"));
  const prompts = [];
  const script = ["not json at all", JSON.stringify(fixture)];
  const { attempts } = await expand({
    doc: minimal,
    callModel: async (prompt, { attempt }) => { prompts.push(prompt); return script[attempt - 1]; },
    model: "manual",
    at: "2026-08-22T21:00:00Z",
  });
  check("second prompt carries the validation error text",
    attempts === 2 && prompts[1].user.includes("previous attempt failed validation") && prompts[1].user.includes("not parseable JSON"));
}

// Provenance claim override: no --manual-model flag exists — "manual" is the
// only stamp. Pinned so an override, if ever added, lands deliberately.
{
  check("manual stamp is always \"manual\" (no override flag exists)",
    JSON.parse(ok.stdout).metadata.interpreter.model === "manual");
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
